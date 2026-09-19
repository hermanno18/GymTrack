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
**Important: all active development currently lives on the `dev` branch --
`main` doesn't exist on GitHub yet.** Point cPanel at `dev` for now, or
create/merge into `main` yourself first if you'd rather keep a clean
prod-only branch (`git checkout -b main && git push origin main` from
`dev`, then repoint cPanel at `main` later). Either way:

- Use cPanel's **Git Version Control** feature to pull directly from
  `https://github.com/hermanno18/GymTrack.git`, branch **`dev`** (or
  `main`, once you've created it), or
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
