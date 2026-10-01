"""
Minimal outbound email for password-reset links.

No third-party mail library -- the only email need in this app is a
single transactional message type, so plain stdlib smtplib is enough.
Configured entirely via environment variables (same pattern as
SECRET_KEY/DATABASE_URL in app/__init__.py) so pointing this at a real
mailbox in production is a cPanel env-var change, not a code change.

If SMTP_HOST isn't configured (local dev, or before an admin has set
up a mailbox), the reset link is logged to the console instead of
actually emailed -- the forgot-password flow still works end-to-end
for local testing, it just prints the link instead of sending it.
"""
import os
import smtplib
from email.message import EmailMessage


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
        print(f"[GymTrack] SMTP_HOST not configured -- would have emailed {to_email}:\n{body}")
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

    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_cls(host, port, timeout=10) as server:
        if not use_ssl:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)
    return True
