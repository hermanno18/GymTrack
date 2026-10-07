"""
Shared pytest fixtures.

CSRF is disabled for the functional-test app fixture to keep test code
focused on business logic -- see tests/test_csrf.py for a dedicated
regression check that CSRF protection is actually wired up.
"""
import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
    })
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def register(client):
    """Factory fixture: register (and log in) a user, return the response."""
    def _register(email="user@example.com", password="testpass123"):
        return client.post(
            "/auth/register",
            data={"email": email, "password": password, "confirm": password},
            follow_redirects=True,
        )
    return _register
