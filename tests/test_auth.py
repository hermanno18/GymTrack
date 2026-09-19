"""Auth flow tests: registration validation, login/logout, access control."""


def test_dashboard_requires_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_register_creates_user_and_logs_in(client, register):
    resp = register(email="new@example.com", password="testpass123")
    assert resp.status_code == 200
    # Landed on dashboard, not bounced back to register
    assert b"Dashboard" in resp.data


def test_register_rejects_short_password(client):
    resp = client.post("/auth/register", data={
        "email": "short@example.com", "password": "abc", "confirm": "abc",
    }, follow_redirects=True)
    assert b"at least 8 characters" in resp.data


def test_register_rejects_mismatched_passwords(client):
    resp = client.post("/auth/register", data={
        "email": "mismatch@example.com", "password": "testpass123", "confirm": "different123",
    }, follow_redirects=True)
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data


def test_register_rejects_duplicate_email(client, register):
    register(email="dupe@example.com")
    client.get("/auth/logout")
    resp = client.post("/auth/register", data={
        "email": "dupe@example.com", "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)
    assert b"already exists" in resp.data


def test_login_wrong_password(client, register):
    register(email="loginuser@example.com", password="correctpass1")
    client.get("/auth/logout")
    resp = client.post("/auth/login", data={
        "email": "loginuser@example.com", "password": "wrongpass",
    }, follow_redirects=True)
    assert b"Invalid email or password" in resp.data


def test_login_success_after_logout(client, register):
    register(email="loginuser2@example.com", password="correctpass1")
    client.get("/auth/logout")
    resp = client.post("/auth/login", data={
        "email": "loginuser2@example.com", "password": "correctpass1",
    }, follow_redirects=True)
    assert b"Dashboard" in resp.data
