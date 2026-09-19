"""
Multi-user data isolation tests.

This is the single most important security property of a multi-user app:
one user should never be able to see, edit, or delete another user's data.
Kept in its own file since it's a cross-cutting concern, not tied to one
blueprint.
"""
from app.models import Program


def _register(client, email):
    return client.post("/auth/register", data={
        "email": email, "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)


def test_program_list_is_scoped_per_user(app):
    client_a = app.test_client()
    client_b = app.test_client()
    _register(client_a, "alice@example.com")
    _register(client_b, "bob@example.com")

    client_a.post("/programs/new/manual", data={"name": "Alice Program"}, follow_redirects=True)

    resp_b = client_b.get("/programs/")
    assert b"Alice Program" not in resp_b.data

    resp_a = client_a.get("/programs/")
    assert b"Alice Program" in resp_a.data


def test_user_cannot_view_another_users_program_builder(app):
    client_a = app.test_client()
    client_b = app.test_client()
    _register(client_a, "alice2@example.com")
    _register(client_b, "bob2@example.com")

    client_a.post("/programs/new/manual", data={"name": "Alice Secret Plan"}, follow_redirects=True)
    with app.app_context():
        program = Program.query.filter_by(name="Alice Secret Plan").first()

    resp = client_b.get(f"/programs/{program.id}/builder")
    assert resp.status_code == 404


def test_user_cannot_delete_another_users_program(app):
    client_a = app.test_client()
    client_b = app.test_client()
    _register(client_a, "alice3@example.com")
    _register(client_b, "bob3@example.com")

    client_a.post("/programs/new/manual", data={"name": "Alice Plan 3"}, follow_redirects=True)
    with app.app_context():
        program = Program.query.filter_by(name="Alice Plan 3").first()

    resp = client_b.post(f"/programs/{program.id}/delete")
    assert resp.status_code == 404

    # still exists for Alice
    with app.app_context():
        from app import db
        assert db.session.get(Program, program.id) is not None


def test_exercise_suggestions_dont_leak_across_users(app):
    client_a = app.test_client()
    client_b = app.test_client()
    _register(client_a, "alice4@example.com")
    _register(client_b, "bob4@example.com")

    client_a.post("/programs/new/manual", data={"name": "Alice Plan 4"}, follow_redirects=True)
    with app.app_context():
        program = Program.query.filter_by(name="Alice Plan 4").first()
    client_a.post(f"/programs/{program.id}/days", data={"label": "Day 1"}, follow_redirects=True)
    with app.app_context():
        from app.models import ProgramDay
        day = ProgramDay.query.filter_by(program_id=program.id).first()
    client_a.post(f"/days/{day.id}/exercises", data={"name": "Squat", "sets": 4, "reps": 8})

    # Bob has no exercises yet -- suggestion lookup for "Squat" should find nothing of Alice's
    resp = client_b.get("/exercises/suggest?name=Squat")
    assert resp.data.strip() == b""
