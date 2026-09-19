"""
Dedicated CSRF regression test. Every other test file disables CSRF
(see conftest.py) to keep business-logic tests readable -- this file is
the one place that re-enables it, to guard against ever silently losing
that protection again.
"""
import re

from app import create_app


def test_post_without_csrf_token_is_rejected(tmp_path):
    db_path = tmp_path / "csrf_test.db"
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": True,
        "SECRET_KEY": "test-secret",
    })
    client = app.test_client()

    resp = client.post("/auth/register", data={
        "email": "nocsrf@example.com", "password": "testpass123", "confirm": "testpass123",
    })
    assert resp.status_code == 400


def test_post_with_valid_csrf_token_succeeds(tmp_path):
    db_path = tmp_path / "csrf_test2.db"
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": True,
        "SECRET_KEY": "test-secret",
    })
    client = app.test_client()

    page = client.get("/auth/register").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    resp = client.post("/auth/register", data={
        "csrf_token": token,
        "email": "withcsrf@example.com", "password": "testpass123", "confirm": "testpass123",
    })
    assert resp.status_code == 302
