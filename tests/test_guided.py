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
    assert b"06:00" in resp.data
