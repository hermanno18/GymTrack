"""
Guided Session mode: start a day, get a timer-driven walk through its
exercises, and save the whole thing (with work/rest timing) as a normal
WorkoutSession -- then view it as an animated "story" timeline.
"""
from app.models import Program, ProgramDay, Exercise, WorkoutSession, WorkoutLog


def _register(client, email="guideduser@example.com"):
    return client.post("/auth/register", data={
        "email": email, "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)


def _make_day_with_exercises(client, app, program_name="Guided Program"):
    client.post("/programs/new/manual", data={"name": program_name})
    with app.app_context():
        program = Program.query.filter_by(name=program_name).first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    client.post(f"/days/{day.id}/exercises", data={"name": "Bench Press", "sets": "3", "reps": "8", "weight": "60"})
    client.post(f"/days/{day.id}/exercises", data={"name": "Run", "duration": "20:00"})
    with app.app_context():
        exercises = Exercise.query.filter_by(program_day_id=day.id).order_by(Exercise.order_index).all()
        exercise_ids = [ex.id for ex in exercises]
    return day.id, exercise_ids


def test_session_start_renders_exercise_data(client, app):
    _register(client)
    day_id, _ = _make_day_with_exercises(client, app)
    resp = client.get(f"/guided/{day_id}")
    assert resp.status_code == 200
    assert b"Bench Press" in resp.data
    assert b"guided-root" in resp.data


def test_session_start_redirects_when_day_has_no_exercises(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "Empty Program"})
    with app.app_context():
        program = Program.query.filter_by(name="Empty Program").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    resp = client.get(f"/guided/{day.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"no exercises yet" in resp.data


def test_session_finish_creates_session_and_logs_with_timing(client, app):
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    payload = {
        "start_time": "18:00", "end_time": "18:45",
        "results": [
            {
                "exercise_id": exercise_ids[0], "started_at": "18:00:05",
                "work_seconds": 90, "rest_seconds": 60,
                "sets": "3", "reps": "8", "weight": "62.5", "distance": "",
            },
            {
                "exercise_id": exercise_ids[1], "started_at": "18:05:00",
                "work_seconds": 1200, "rest_seconds": 0,
                "sets": "", "reps": "", "weight": "", "distance": "",
            },
        ],
    }
    resp = client.post(f"/guided/{day_id}/finish", json=payload)
    assert resp.status_code == 200
    redirect_url = resp.get_json()["redirect"]
    assert "/guided/story/" in redirect_url

    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        assert session.start_time == "18:00"
        assert session.end_time == "18:45"
        logs = WorkoutLog.query.filter_by(session_id=session.id).order_by(WorkoutLog.id).all()
        assert len(logs) == 2

        bench_log = logs[0]
        assert bench_log.actual_weight_kg == 62.5
        assert bench_log.work_seconds == 90
        assert bench_log.rest_seconds == 60
        assert bench_log.started_at == "18:00:05"

        run_log = logs[1]
        # A timed exercise's measured work time should double as its duration.
        assert run_log.actual_duration_seconds == 1200
        assert run_log.work_seconds == 1200


def test_session_finish_ignores_exercise_ids_from_other_users(client, app):
    _register(client, email="ownera@example.com")
    day_id, _ = _make_day_with_exercises(client, app, program_name="Owner A Program")

    client.get("/auth/logout")
    _register(client, email="ownerb@example.com")
    _, other_exercise_ids = _make_day_with_exercises(client, app, program_name="Owner B Program")

    # Log back in as owner A (who owns day_id) and try to sneak in owner B's
    # exercise id in the results payload -- it should be silently skipped
    # rather than trusted, even though the day itself belongs to owner A.
    client.get("/auth/logout")
    client.post("/auth/login", data={"email": "ownera@example.com", "password": "testpass123"})
    resp = client.post(f"/guided/{day_id}/finish", json={
        "start_time": "10:00", "end_time": "10:10",
        "results": [{"exercise_id": other_exercise_ids[0], "work_seconds": 30, "rest_seconds": 10}],
    })
    assert resp.status_code == 200
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        assert WorkoutLog.query.filter_by(session_id=session.id).count() == 0


def test_story_page_shows_timing_and_totals(client, app):
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "07:00", "end_time": "07:30",
        "results": [
            {"exercise_id": exercise_ids[0], "started_at": "07:00:00", "work_seconds": 90, "rest_seconds": 45,
             "sets": "3", "reps": "8", "weight": "60"},
        ],
    })
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        session_id = session.id

    resp = client.get(f"/guided/story/{session_id}")
    assert resp.status_code == 200
    assert b"Bench Press" in resp.data
    assert b"1:30" in resp.data  # formatted work_seconds
    assert b"0:45" in resp.data  # formatted rest_seconds
    assert b"Time Working" in resp.data
    assert b"Time Resting" in resp.data


def test_story_page_degrades_gracefully_for_manual_sessions(client, app):
    """A session logged the old-fashioned manual way (no guided-mode
    timing data at all) should still render as a storyline -- just
    without the work/rest time chips, which would otherwise misleadingly
    show '0:00' instead of 'not tracked'."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    log_page = client.get(f"/workouts/log/{day_id}").text
    client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-03-01",
        f"ex_{exercise_ids[0]}_sets": "3", f"ex_{exercise_ids[0]}_reps": "8", f"ex_{exercise_ids[0]}_weight": "60",
    })
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        session_id = session.id

    resp = client.get(f"/guided/story/{session_id}")
    assert resp.status_code == 200
    assert b"Bench Press" in resp.data
    assert b"Time Working" not in resp.data
    assert b"Time Resting" not in resp.data
    assert b"Exercise" in resp.data and b"Logged" in resp.data


def test_story_page_requires_ownership(client, app):
    _register(client, email="storyowner@example.com")
    day_id, exercise_ids = _make_day_with_exercises(client, app, program_name="Story Program")
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "08:00", "end_time": "08:20",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30}],
    })
    with app.app_context():
        session_id = WorkoutSession.query.filter_by(program_day_id=day_id).first().id

    client.get("/auth/logout")
    _register(client, email="intruder@example.com")
    resp = client.get(f"/guided/story/{session_id}")
    assert resp.status_code == 404


def test_guided_session_appears_in_regular_history(client, app):
    """The guided flow writes plain WorkoutSession/WorkoutLog rows, so it
    should show up in the existing History page for free."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "06:00", "end_time": "06:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30, "sets": "3", "reps": "8"}],
    })
    resp = client.get("/workouts/history")
    assert resp.status_code == 200
    assert b"6:00 AM" in resp.data  # 06:00 rendered in friendly 12h format


def test_history_entries_link_to_their_storyline(client, app):
    """Every History tile should link straight into the animated story
    timeline, regardless of whether the session came from guided mode
    or manual logging."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "06:00", "end_time": "06:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30, "sets": "3", "reps": "8"}],
    })
    with app.app_context():
        session_id = WorkoutSession.query.filter_by(program_day_id=day_id).first().id

    resp = client.get("/workouts/history")
    assert f"/guided/story/{session_id}".encode() in resp.data


def test_dashboard_recent_sessions_matches_history_tile_and_links_to_it(client, app):
    """Dashboard's Recent Sessions should render the same story-linked
    tile as History, plus a 'See all' link to the full History page."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "09:00", "end_time": "09:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30, "sets": "3", "reps": "8"}],
    })
    with app.app_context():
        session_id = WorkoutSession.query.filter_by(program_day_id=day_id).first().id

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"See all" in resp.data
    assert f"/guided/story/{session_id}".encode() in resp.data
    assert b"View Story" in resp.data


def test_session_finish_saves_per_exercise_notes(client, app):
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "08:00", "end_time": "08:30",
        "results": [
            {"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30,
             "sets": "3", "reps": "8", "weight": "60", "notes": "  Left shoulder a bit tight  "},
        ],
    })
    with app.app_context():
        log = WorkoutLog.query.filter_by(exercise_id=exercise_ids[0]).first()
        assert log.notes == "Left shoulder a bit tight"


def test_session_finish_blank_notes_stored_as_none(client, app):
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "08:00", "end_time": "08:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30, "notes": "   "}],
    })
    with app.app_context():
        log = WorkoutLog.query.filter_by(exercise_id=exercise_ids[0]).first()
        assert log.notes is None


def test_session_start_has_no_pr_fields_before_any_history(client, app):
    """Brand new exercise, never logged before: no personal-best data
    exists yet, so the PR fields should be null (client falls back to
    the coach's static target)."""
    _register(client)
    day_id, _ = _make_day_with_exercises(client, app)
    resp = client.get(f"/guided/{day_id}")
    assert resp.status_code == 200
    assert b'"pr_weight_display": null' in resp.data


def test_session_start_shows_personal_best_as_target(client, app):
    """Once a heavier weight has been logged than the coach's plan, the
    Guided Session countdown should offer that PR as the new target."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app)
    # Bench Press's program target was 60kg -- log a heavier top set.
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "07:00", "end_time": "07:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30,
                      "sets": "3", "reps": "6", "weight": "70"}],
    })
    resp = client.get(f"/guided/{day_id}")
    assert resp.status_code == 200
    assert b'"pr_weight_display": 70.0' in resp.data
    assert b'"pr_reps": 6' in resp.data


def test_personal_best_carries_over_across_programs(client, app):
    """Same exercise name in a brand new program should still surface the
    PR set under the old program (matches the existing progression-
    carryover behaviour used everywhere else in the app)."""
    _register(client)
    day_id, exercise_ids = _make_day_with_exercises(client, app, program_name="Block 1")
    client.post(f"/guided/{day_id}/finish", json={
        "start_time": "07:00", "end_time": "07:30",
        "results": [{"exercise_id": exercise_ids[0], "work_seconds": 60, "rest_seconds": 30,
                      "sets": "3", "reps": "6", "weight": "70"}],
    })
    new_day_id, _ = _make_day_with_exercises(client, app, program_name="Block 2")
    resp = client.get(f"/guided/{new_day_id}")
    assert resp.status_code == 200
    assert b'"pr_weight_display": 70.0' in resp.data
