"""
Workout logging + progression tests, including the flagship feature:
history carrying over automatically when an exercise name matches across
different programs.
"""
from app.models import Program, ProgramDay, Exercise, WorkoutSession, WorkoutLog


def _register(client, email="workoutuser@example.com"):
    return client.post("/auth/register", data={
        "email": email, "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)


def _make_program_with_exercise(client, app, program_name, day_label, exercise_name, **fields):
    client.post("/programs/new/manual", data={"name": program_name})
    with app.app_context():
        program = Program.query.filter_by(name=program_name).first()
    client.post(f"/programs/{program.id}/days", data={"label": day_label})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    payload = {"name": exercise_name}
    payload.update(fields)
    client.post(f"/days/{day.id}/exercises", data=payload)
    with app.app_context():
        exercise = Exercise.query.filter_by(program_day_id=day.id, name=exercise_name).first()
    return program.id, day.id, exercise.id


def test_log_against_planned_day(client, app):
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(
        client, app, "Program A", "Day 1", "Bench Press", sets="4", reps="8", weight="60"
    )
    resp = client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-01-10",
        f"ex_{ex_id}_sets": "4",
        f"ex_{ex_id}_reps": "8",
        f"ex_{ex_id}_weight": "62.5",
    }, follow_redirects=True)
    assert b"Workout logged" in resp.data
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        log = WorkoutLog.query.filter_by(session_id=session.id).first()
        assert log.actual_weight_kg == 62.5
        assert log.actual_sets == 4


def test_skips_exercise_with_no_data_entered(client, app):
    _register(client)
    _, day_id, _ = _make_program_with_exercise(client, app, "Program B", "Day 1", "Squat")
    client.post(f"/workouts/log/{day_id}", data={"date": "2026-01-10"}, follow_redirects=True)
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        assert WorkoutLog.query.filter_by(session_id=session.id).count() == 0


def test_adhoc_logging_creates_new_exercise(client, app):
    _register(client)
    resp = client.post("/workouts/log/adhoc", data={
        "date": "2026-01-11",
        "adhoc_name": "Kettlebell Swing",
        "adhoc_sets": "3",
        "adhoc_reps": "15",
    }, follow_redirects=True)
    assert b"Workout logged" in resp.data
    with app.app_context():
        exercise = Exercise.query.filter_by(name_normalized="kettlebell swing").first()
        assert exercise is not None
        log = WorkoutLog.query.filter_by(exercise_id=exercise.id).first()
        assert log.actual_reps == 15


def test_adhoc_logging_reuses_existing_exercise_by_name(client, app):
    _register(client)
    _make_program_with_exercise(client, app, "Program C", "Day 1", "Deadlift")
    client.post("/workouts/log/adhoc", data={
        "date": "2026-01-12",
        "adhoc_name": "deadlift",  # different case -- should match by normalized name
        "adhoc_sets": "3", "adhoc_reps": "5",
    })
    with app.app_context():
        matches = Exercise.query.filter_by(name_normalized="deadlift").all()
        assert len(matches) == 1  # reused, not duplicated
        assert WorkoutLog.query.filter_by(exercise_id=matches[0].id).count() == 1


def test_progression_history_carries_over_across_programs(client, app):
    _register(client)
    _, day1_id, ex1_id = _make_program_with_exercise(client, app, "Block 1", "Day 1", "Bench Press", weight="60")
    client.post(f"/workouts/log/{day1_id}", data={"date": "2026-01-01", f"ex_{ex1_id}_weight": "60"})

    _, day2_id, ex2_id = _make_program_with_exercise(client, app, "Block 2", "Day 1", "Bench Press", weight="65")
    client.post(f"/workouts/log/{day2_id}", data={"date": "2026-02-01", f"ex_{ex2_id}_weight": "65"})

    resp = client.get("/workouts/progress/bench press")
    assert resp.status_code == 200
    assert b"60.0" in resp.data
    assert b"65.0" in resp.data


def test_weight_unit_conversion_in_logging(client, app):
    _register(client)
    client.post("/settings/", data={"weight_unit": "lb", "distance_unit": "mi"})
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program D", "Day 1", "Overhead Press")
    client.post(f"/workouts/log/{day_id}", data={"date": "2026-01-15", f"ex_{ex_id}_weight": "100"})  # 100 lb
    with app.app_context():
        log = WorkoutLog.query.first()
        assert round(log.actual_weight_kg, 2) == round(100 * 0.45359237, 2)


def test_session_start_and_end_time_are_saved(client, app):
    _register(client)
    resp = client.post("/workouts/log/adhoc", data={
        "date": "2026-01-20", "start_time": "18:00", "end_time": "19:15",
        "adhoc_name": "Row", "adhoc_duration": "20:00",
    }, follow_redirects=True)
    assert b"Workout logged" in resp.data
    with app.app_context():
        session = WorkoutSession.query.filter_by(user_id=1).first()
        assert session.start_time == "18:00"
        assert session.end_time == "19:15"


def test_planned_exercise_duration_is_logged(client, app):
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program E", "Day 1", "Run")
    client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-01-21", f"ex_{ex_id}_duration": "24:30",
    })
    with app.app_context():
        log = WorkoutLog.query.filter_by(exercise_id=ex_id).first()
        assert log.actual_duration_seconds == 24 * 60 + 30


def test_duration_only_entry_is_not_skipped(client, app):
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program F", "Day 1", "Row")
    client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-01-22", f"ex_{ex_id}_duration": "5:00",
    })
    with app.app_context():
        session = WorkoutSession.query.filter_by(program_day_id=day_id).first()
        assert WorkoutLog.query.filter_by(session_id=session.id).count() == 1


def test_adhoc_duration_is_logged(client, app):
    _register(client)
    client.post("/workouts/log/adhoc", data={
        "date": "2026-01-23", "adhoc_name": "Row 500m", "adhoc_duration": "1:45",
    })
    with app.app_context():
        exercise = Exercise.query.filter_by(name_normalized="row 500m").first()
        log = WorkoutLog.query.filter_by(exercise_id=exercise.id).first()
        assert log.actual_duration_seconds == 105


def test_invalid_duration_format_is_ignored_not_crashed(client, app):
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program G", "Day 1", "Run")
    resp = client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-01-24", f"ex_{ex_id}_sets": "1", f"ex_{ex_id}_duration": "garbage",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        log = WorkoutLog.query.filter_by(exercise_id=ex_id).first()
        assert log.actual_duration_seconds is None


def test_duration_becomes_progress_metric_when_no_weight_or_distance(client, app):
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program H", "Day 1", "Plank")
    client.post(f"/workouts/log/{day_id}", data={"date": "2026-01-25", f"ex_{ex_id}_duration": "1:30"})
    resp = client.get("/workouts/progress/plank")
    assert resp.status_code == 200
    assert b'"value": 90' in resp.data


def test_progress_detail_exposes_multiple_metrics_when_available(client, app):
    """
    An exercise logged with both weight AND reps should chart both --
    the old behaviour silently picked one metric and threw the other away.
    """
    _register(client)
    _, day_id, ex_id = _make_program_with_exercise(client, app, "Program I", "Day 1", "Squat")
    client.post(f"/workouts/log/{day_id}", data={
        "date": "2026-01-26", f"ex_{ex_id}_sets": "3", f"ex_{ex_id}_reps": "5", f"ex_{ex_id}_weight": "80",
    })
    resp = client.get("/workouts/progress/squat")
    assert resp.status_code == 200
    assert b'"weight"' in resp.data
    assert b'"reps"' in resp.data
    assert b'"sets"' in resp.data
    assert b'metric-tab' in resp.data  # the switcher UI is present
