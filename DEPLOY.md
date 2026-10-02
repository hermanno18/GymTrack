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

## 2. Get the code onto the server (one-time Git Version Control setup)
**`main` is the deploy branch.** Active day-to-day development happens on
`dev` -- `main` only moves forward when you deliberately merge a release
cut into it. This keeps "what's live" and "what's in progress" cleanly
separated, and means a half-finished `dev` change never accidentally ships.

1. cPanel -> **Git Version Control** -> **Create**
2. **Clone URL**: `https://github.com/hermanno18/GymTrack.git`
3. **Repository Path**: `/home/<user>/gymtrack` (must match the Application
   root from Step 1 exactly)
4. **Branch**: `main`
5. Click **Create**

## 3. One-click deploy via `.cpanel.yml`
This repo ships a `.cpanel.yml` + `scripts/cpanel-deploy.sh` pair that
automates dependency installs and restarting the app, so you no longer
need to SSH in by hand for every deploy.

Open `scripts/cpanel-deploy.sh` and fill in the two placeholder values near
the top, once:
```bash
CPANEL_USERNAME="REPLACE_ME_USERNAME"        # your actual cPanel username
PYTHON_VERSION="REPLACE_ME_PYTHON_VERSION"   # e.g. 3.11 (from Step 1's app page)
```
Commit and push that change once -- it's account-specific config, not a
secret, so it's fine to commit. `.cpanel.yml` itself never needs editing;
it just calls this script. Logic lives in one self-contained script
specifically because **cPanel runs each `.cpanel.yml` task line as its own
isolated shell** -- a variable exported on one line would NOT carry over
to the next, so keeping it all in one script sidesteps that entirely.

### Every deploy after that
1. Merge your changes into `main` and push to GitHub
2. cPanel -> **Git Version Control** -> your repo -> **Manage**
3. Click **Update from Remote** (pulls the latest commit)
4. Click **Deploy HEAD Commit**

That's it -- the `.cpanel.yml` task activates the venv, runs
`pip install -r requirements.txt`, and touches `tmp/restart.txt` so
Passenger picks up the new code immediately.

### If something goes wrong with the automated deploy
Fall back to doing it by hand via cPanel -> **Terminal**:
```bash
source /home/<user>/virtualenv/gymtrack/<python-version>/bin/activate
cd /home/<user>/gymtrack
git pull
pip install -r requirements.txt
touch tmp/restart.txt
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

## 6. Restart (first time only)
Back on the Setup Python App page, click **Restart** once, after the
initial Git pull + `pip install` + env vars are all in place. Visit your
subdomain to confirm it's live. From here on, every future deploy's
restart is handled automatically by `scripts/cpanel-deploy.sh` (Step 3) --
you shouldn't need to click Restart manually again.

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
  requirements.txt` after switching (or just trigger a deploy via
  Step 3 -- it reinstalls dependencies every time anyway).
