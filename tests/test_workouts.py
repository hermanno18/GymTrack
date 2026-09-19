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
