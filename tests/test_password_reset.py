"""
Forgot-password email flow.

Tokens are self-invalidating (itsdangerous-signed, embedding a slice of
the current password hash as a fingerprint) -- no database table of
issued/used tokens is needed; using a token to reset the password
automatically invalidates that same token for any future reuse.

The actual mailer (app/mailer.py) is monkeypatched here instead of
sending real email -- see app.auth.send_password_reset_email, which is
imported into app.auth's namespace and therefore what we patch.
"""
from app import auth as auth_module


def _register(client, email="resetuser@example.com", password="testpass123"):
    return client.post("/auth/register", data={
        "email": email, "password": password, "confirm": password,
    }, follow_redirects=True)


def _capture_reset_email(monkeypatch):
    captured = {}

    def fake_send(to_email, reset_url):
        captured["to_email"] = to_email
        captured["reset_url"] = reset_url
        return True

    monkeypatch.setattr(auth_module, "send_password_reset_email", fake_send)
    return captured


def _token_from_url(reset_url):
    return reset_url.rsplit("/", 1)[-1]


def test_forgot_password_sends_reset_link_for_known_email(client, app, monkeypatch):
    _register(client)
    client.get("/auth/logout")
    captured = _capture_reset_email(monkeypatch)

    resp = client.post("/auth/forgot", data={"email": "resetuser@example.com"}, follow_redirects=True)
    assert resp.status_code == 200
    assert captured.get("to_email") == "resetuser@example.com"
    assert "/auth/reset/" in captured.get("reset_url", "")


def test_forgot_password_does_not_leak_whether_email_exists(client, monkeypatch):
    captured = _capture_reset_email(monkeypatch)
    resp = client.post("/auth/forgot", data={"email": "nosuchuser@example.com"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "reset_url" not in captured  # no email actually sent for an unknown address
    assert b"reset link is on its way" in resp.data  # same generic message either way


def test_reset_link_allows_setting_new_password_and_logging_in(client, app, monkeypatch):
    _register(client)
    client.get("/auth/logout")
    captured = _capture_reset_email(monkeypatch)
    client.post("/auth/forgot", data={"email": "resetuser@example.com"})
    token = _token_from_url(captured["reset_url"])

    resp = client.post(f"/auth/reset/{token}", data={
        "password": "brandnewpass1", "confirm": "brandnewpass1",
    }, follow_redirects=True)
    assert b"Password reset" in resp.data

    resp = client.post("/auth/login", data={
        "email": "resetuser@example.com", "password": "brandnewpass1",
    })
    assert resp.status_code == 302  # logged in -> redirected to dashboard

    client.get("/auth/logout")
    resp = client.post("/auth/login", data={
        "email": "resetuser@example.com", "password": "testpass123",
    })
    assert b"Invalid email or password" in resp.data  # old password no longer works


def test_reset_rejects_mismatched_new_passwords(client, app, monkeypatch):
    _register(client)
    client.get("/auth/logout")
    captured = _capture_reset_email(monkeypatch)
    client.post("/auth/forgot", data={"email": "resetuser@example.com"})
    token = _token_from_url(captured["reset_url"])

    resp = client.post(f"/auth/reset/{token}", data={
        "password": "brandnewpass1", "confirm": "different123",
    }, follow_redirects=True)
    assert b"don&#39;t match" in resp.data or b"don't match" in resp.data


def test_reset_rejects_too_short_new_password(client, app, monkeypatch):
    _register(client)
    client.get("/auth/logout")
    captured = _capture_reset_email(monkeypatch)
    client.post("/auth/forgot", data={"email": "resetuser@example.com"})
    token = _token_from_url(captured["reset_url"])

    resp = client.post(f"/auth/reset/{token}", data={
        "password": "short", "confirm": "short",
    }, follow_redirects=True)
    assert b"at least 8 characters" in resp.data


def test_reset_token_cannot_be_reused_after_a_successful_reset(client, app, monkeypatch):
    """Self-invalidating: resetting the password changes the hash the
    token's fingerprint was built against, so a second use fails."""
    _register(client)
    client.get("/auth/logout")
    captured = _capture_reset_email(monkeypatch)
    client.post("/auth/forgot", data={"email": "resetuser@example.com"})
    token = _token_from_url(captured["reset_url"])

    client.post(f"/auth/reset/{token}", data={"password": "firstnewpass1", "confirm": "firstnewpass1"})
    resp = client.post(f"/auth/reset/{token}", data={
        "password": "secondnewpass1", "confirm": "secondnewpass1",
    }, follow_redirects=True)
    assert b"invalid or has expired" in resp.data


def test_reset_rejects_garbage_token(client, app):
    resp = client.get("/auth/reset/not-a-real-token", follow_redirects=True)
    assert resp.status_code == 200
    assert b"invalid or has expired" in resp.data


def test_login_page_links_to_forgot_password(client):
    resp = client.get("/auth/login")
    assert b'href="/auth/forgot"' in resp.data


def test_mailer_falls_back_to_logging_without_smtp_host(monkeypatch, caplog):
    """When SMTP_HOST isn't configured (local dev, or before an admin
    sets up a mailbox), sending degrades to a logged warning instead of
    raising -- the flow should never crash just because email isn't
    wired up yet."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    from app.mailer import send_password_reset_email
    with caplog.at_level("WARNING"):
        result = send_password_reset_email("someone@example.com", "http://example.com/auth/reset/abc")
    assert result is False
    assert "someone@example.com" in caplog.text


def test_mailer_handles_smtp_failure_gracefully(monkeypatch, caplog):
    """A transient SMTP outage should be logged and return False, never
    raise -- the forgot-password route must always show its generic
    success message regardless of whether sending actually worked.
    Mocks smtplib directly so this doesn't depend on real network/DNS
    behavior (fast and deterministic either way)."""
    import app.mailer as mailer_module

    class _ExplodingSMTP:
        def __init__(self, *args, **kwargs):
            raise OSError("connection refused (simulated)")

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(mailer_module.smtplib, "SMTP", _ExplodingSMTP)

    with caplog.at_level("ERROR"):
        result = mailer_module.send_password_reset_email(
            "someone@example.com", "http://example.com/auth/reset/abc"
        )
    assert result is False
    assert "Failed to send" in caplog.text
