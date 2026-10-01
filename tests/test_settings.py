"""
Account settings: unit preferences, change email, change password.
All three forms share the /settings/ POST route, routed by a hidden
form_name field (see app/settings.py).
"""
from app.models import User


def _register(client, email="settingsuser@example.com", password="testpass123"):
    return client.post("/auth/register", data={
        "email": email, "password": password, "confirm": password,
    }, follow_redirects=True)


def test_units_form_updates_preferences(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "units", "weight_unit": "lb", "distance_unit": "mi",
    }, follow_redirects=True)
    assert b"Settings saved" in resp.data
    with app.app_context():
        user = User.query.filter_by(email="settingsuser@example.com").first()
        assert user.settings.weight_unit == "lb"
        assert user.settings.distance_unit == "mi"


def test_change_email_requires_correct_current_password(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "email", "new_email": "new@example.com", "current_password": "wrongpass",
    }, follow_redirects=True)
    assert b"Current password is incorrect" in resp.data
    with app.app_context():
        assert User.query.filter_by(email="settingsuser@example.com").first() is not None
        assert User.query.filter_by(email="new@example.com").first() is None


def test_change_email_success(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "email", "new_email": "updated@example.com", "current_password": "testpass123",
    }, follow_redirects=True)
    assert b"Email updated" in resp.data
    with app.app_context():
        assert User.query.filter_by(email="updated@example.com").first() is not None
        assert User.query.filter_by(email="settingsuser@example.com").first() is None


def test_change_email_rejects_duplicate(client, app):
    _register(client, email="first@example.com")
    client.get("/auth/logout")
    _register(client, email="second@example.com")
    resp = client.post("/settings/", data={
        "form_name": "email", "new_email": "first@example.com", "current_password": "testpass123",
    }, follow_redirects=True)
    assert b"already in use" in resp.data
    with app.app_context():
        user = User.query.filter_by(email="second@example.com").first()
        assert user is not None  # unchanged


def test_change_email_rejects_invalid_format(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "email", "new_email": "not-an-email", "current_password": "testpass123",
    }, follow_redirects=True)
    assert b"valid email" in resp.data


def test_change_password_requires_correct_current_password(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "password", "current_password": "wrongpass",
        "new_password": "newpass123", "confirm_password": "newpass123",
    }, follow_redirects=True)
    assert b"Current password is incorrect" in resp.data


def test_change_password_rejects_mismatched_confirmation(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "password", "current_password": "testpass123",
        "new_password": "newpass123", "confirm_password": "different123",
    }, follow_redirects=True)
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data


def test_change_password_rejects_too_short(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "password", "current_password": "testpass123",
        "new_password": "short", "confirm_password": "short",
    }, follow_redirects=True)
    assert b"at least 8 characters" in resp.data


def test_change_password_success_and_can_login_with_new_password(client, app):
    _register(client)
    resp = client.post("/settings/", data={
        "form_name": "password", "current_password": "testpass123",
        "new_password": "brandnewpass1", "confirm_password": "brandnewpass1",
    }, follow_redirects=True)
    assert b"Password updated" in resp.data

    client.get("/auth/logout")
    resp = client.post("/auth/login", data={
        "email": "settingsuser@example.com", "password": "brandnewpass1",
    }, follow_redirects=True)
    assert b"Invalid email or password" not in resp.data

    # Old password should no longer work.
    client.get("/auth/logout")
    resp = client.post("/auth/login", data={
        "email": "settingsuser@example.com", "password": "testpass123",
    })
    assert b"Invalid email or password" in resp.data
