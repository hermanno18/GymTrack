# Deploying GymTrack on WHC (cPanel / Passenger)

GymTrack is built as a plain **WSGI Flask app** specifically so it runs
natively on cPanel's "Setup Python App" feature (Phusion Passenger) --
no ASGI server, no extra bridge needed.

## 1. Create the Python App in cPanel
1. cPanel → **Software → Setup Python App** → **Create Application**.
2. Python version: pick the highest 3.x available (check what's offered;
   anything 3.9+ works).
3. Application root: e.g. `gymtrack` (this becomes a folder under your home dir).
4. Application URL: your subdomain (e.g. `gymtrack.yourdomain.com`).
5. Application startup file: `passenger_wsgi.py`
6. Application Entry point: `application`
7. Click **Create**.

## 2. Get the code onto the server
**Active development lives on the `dev` branch.** A `main` branch also
exists on GitHub, but it's a point-in-time snapshot that isn't kept in
sync automatically -- treat `dev` as the branch to deploy from unless
you've deliberately merged `dev` into `main` for a release cut. Either
way:

- Use cPanel's **Git Version Control** feature to pull directly from
  `https://github.com/hermanno18/GymTrack.git`, branch **`dev`** (or
  `main`, if you've merged a release into it), or
- Upload the repo contents via File Manager / SFTP into the application root
  (make sure `static/images/*.jpg` come along too -- they're tracked in git
  like any other file, no special step needed either way).

## 3. Install dependencies
cPanel's Python App page gives you a command like:
```bash
source /home/<user>/virtualenv/gymtrack/3.x/bin/activate && cd /home/<user>/gymtrack
```
Run that, then:
```bash
pip install -r requirements.txt
```

## 4. Set environment variables
In the cPanel Python App UI, add:
- `SECRET_KEY` — a long random string (used to sign session cookies)
- `SESSION_COOKIE_SECURE` — set to `true` once HTTPS/AutoSSL is
  confirmed working on the domain (makes the session cookie HTTPS-only).
  **Leave unset/false until then** -- a Secure cookie sent over plain
  HTTP is silently dropped by the browser, which breaks login.

To enable the "forgot password" email flow, also add (optional --
without these, reset links are logged to the app's log file instead of
being emailed, which still works for testing but not for real users):
- `SMTP_HOST` — e.g. `mail.yourdomain.com` (your cPanel mailbox's SMTP server)
- `SMTP_PORT` — `587` for STARTTLS (typical) or `465` for implicit SSL
- `SMTP_USERNAME` — full mailbox address, e.g. `noreply@yourdomain.com`
- `SMTP_PASSWORD` — that mailbox's password
- `SMTP_FROM_EMAIL` — optional, defaults to `SMTP_USERNAME` if unset
- `SMTP_USE_SSL` — optional, set to `true` only if using port 465

## 5. Point the subdomain + SSL
1. cPanel → **Domains** → create the subdomain if you haven't already,
   pointing at the same application root.
2. cPanel → **SSL/TLS Status** → run AutoSSL for the subdomain (usually free).

## 6. Restart
Back on the Setup Python App page, click **Restart**. Visit your subdomain.

## Notes
- The SQLite DB and any uploaded PDFs live under `instance/`, which sits
  outside any statically-served directory by default -- don't move it
  into a public `htdocs`/`public_html` path.
- Passenger routes every request (including `/static/...`) through the
  Flask app itself -- there's no separate Apache static-file alias to
  configure. This is fine at this app's scale (a handful of users); if
  it ever needs to serve heavier traffic, point Apache/LiteSpeed at
  `static/` directly instead for better performance.
- If cPanel's Python App version changes later, re-run `pip install -r
  requirements.txt` after switching.
