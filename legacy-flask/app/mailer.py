"""
Minimal outbound email for password-reset links.

No third-party mail library -- the only email need in this app is a
single transactional message type, so plain stdlib smtplib is enough.
Configured entirely via environment variables (same pattern as
SECRET_KEY/DATABASE_URL in app/__init__.py) so pointing this at a real
mailbox in production is a cPanel env-var change, not a code change.

If SMTP_HOST isn't configured (local dev, or before an admin has set
up a mailbox), the reset link is logged instead of actually emailed --
the forgot-password flow still works end-to-end for local testing, it
just logs the link instead of sending it.

Uses the stdlib `logging` module rather than `print()`: Python's
logging has a built-in "handler of last resort" that writes WARNING+
to stderr even with zero configuration, and stderr is what cPanel/
Passenger actually captures into the app's error log -- stdout from a
WSGI app is much less reliably captured. Deliberately not using Flask's
`current_app.logger` here so this module has no Flask dependency and
stays trivially testable/importable on its own.
"""
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email, reset_url):
    subject = "Reset your GymTrack password"
    body = (
        "Someone (hopefully you) requested a password reset for GymTrack.\n\n"
        f"Reset your password here (link expires in 30 minutes):\n{reset_url}\n\n"
        "If you didn't request this, you can safely ignore this email -- "
        "your password won't change unless you click the link above."
    )
    return _send(to_email, subject, body)


def _send(to_email, subject, body):
    host = os.environ.get("SMTP_HOST")
    if not host:
        logger.warning(
            "SMTP_HOST not configured -- would have emailed %s:\n%s", to_email, body
        )
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("SMTP_FROM_EMAIL", username or "noreply@gymtrack.local")
    use_ssl = os.environ.get("SMTP_USE_SSL", "").lower() in ("1", "true", "yes") or port == 465

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(host, port, timeout=10) as server:
            if not use_ssl:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError):
        # A transient mail-server hiccup should never surface as a 500
        # to the user -- the forgot-password route always shows the
        # same generic "a reset link is on its way" message regardless
        # of whether sending actually succeeded, so swallowing this
        # here (after logging it loudly) is the correct behavior, not
        # error-hiding.
        logger.exception("Failed to send password reset email to %s", to_email)
        return False

    return True
