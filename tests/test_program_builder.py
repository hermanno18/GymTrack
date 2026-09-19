"""
Program builder tests: manual creation, day/exercise CRUD, duplicate-name
suggestions. This is the screen used both for from-scratch programs and
for reviewing PDF-extracted ones (see test_pdf_upload.py for that path).
"""
from app.models import Program, ProgramDay, Exercise


def _register(client, email="builderuser@example.com"):
    return client.post("/auth/register", data={
        "email": email, "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)


def test_manual_program_creation_starts_empty(client, app):
    _register(client)
    resp = client.post("/programs/new/manual", data={"name": "My Program"}, follow_redirects=True)
    assert b"My Program" in resp.data
    with app.app_context():
        program = Program.query.filter_by(name="My Program").first()
        assert program is not None
        assert program.days == []


def test_add_day_and_exercise(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "P1"})
    with app.app_context():
        program = Program.query.filter_by(name="P1").first()

    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
        assert day.label == "Day 1"

    resp = client.post(f"/days/{day.id}/exercises", data={
        "name": "Squat", "sets": "4", "reps": "8", "weight": "60", "category": "strength",
    }, follow_redirects=True)
    assert b"Squat" in resp.data
    with app.app_context():
        exercise = Exercise.query.filter_by(program_day_id=day.id).first()
        assert exercise.name == "Squat"
        assert exercise.target_weight_kg == 60.0
        assert exercise.name_normalized == "squat"


def test_add_exercise_requires_name(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "P2"})
    with app.app_context():
        program = Program.query.filter_by(name="P2").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()

    client.post(f"/days/{day.id}/exercises", data={"name": ""}, follow_redirects=True)
    with app.app_context():
        assert Exercise.query.filter_by(program_day_id=day.id).count() == 0


def test_weight_stored_in_kg_regardless_of_display_unit(client, app):
    _register(client)
    client.post("/settings/", data={"weight_unit": "lb", "distance_unit": "mi"})
    client.post("/programs/new/manual", data={"name": "P3"})
    with app.app_context():
        program = Program.query.filter_by(name="P3").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()

    client.post(f"/days/{day.id}/exercises", data={"name": "Bench", "weight": "100"})  # 100 lb
    with app.app_context():
        exercise = Exercise.query.filter_by(program_day_id=day.id).first()
        assert round(exercise.target_weight_kg, 2) == round(100 * 0.45359237, 2)


def test_delete_exercise_and_day(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "P4"})
    with app.app_context():
        program = Program.query.filter_by(name="P4").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    client.post(f"/days/{day.id}/exercises", data={"name": "Squat"})
    with app.app_context():
        exercise = Exercise.query.filter_by(program_day_id=day.id).first()

    resp = client.post(f"/exercises/{exercise.id}/delete")
    assert resp.status_code == 200
    with app.app_context():
        assert Exercise.query.filter_by(program_day_id=day.id).count() == 0

    resp2 = client.post(f"/days/{day.id}/delete")
    assert resp2.status_code == 200
    with app.app_context():
        assert ProgramDay.query.filter_by(id=day.id).first() is None


def test_suggestion_excludes_self_when_editing(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "P5"})
    with app.app_context():
        program = Program.query.filter_by(name="P5").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    client.post(f"/days/{day.id}/exercises", data={"name": "Squat"})
    with app.app_context():
        exercise = Exercise.query.filter_by(program_day_id=day.id).first()

    # Editing the exact same exercise and re-checking its own name shouldn't
    # trigger a "did you mean yourself?" suggestion.
    resp = client.get(f"/exercises/suggest?name=Squat&exclude_id={exercise.id}")
    assert resp.data.strip() == b""


def test_suggestion_flags_near_duplicate(client, app):
    _register(client)
    client.post("/programs/new/manual", data={"name": "P6"})
    with app.app_context():
        program = Program.query.filter_by(name="P6").first()
    client.post(f"/programs/{program.id}/days", data={"label": "Day 1"})
    with app.app_context():
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    client.post(f"/days/{day.id}/exercises", data={"name": "Bench Press"})

    resp = client.get("/exercises/suggest?name=Bench+Pres")
    assert b"Bench Press" in resp.data
