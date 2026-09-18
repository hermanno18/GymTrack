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
Either:
- Use cPanel's **Git Version Control** feature to pull directly from
  `https://github.com/hermanno18/GymTrack.git` (point it at the `main`
  branch), or
- Upload the repo contents via File Manager / SFTP into the application root.

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
- If cPanel's Python App version changes later, re-run `pip install -r
  requirements.txt` after switching.
