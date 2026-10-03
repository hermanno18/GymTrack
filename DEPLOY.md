# Deploying GymTrack on WHC (cPanel / Passenger / LiteSpeed)

GymTrack is built as a plain **WSGI Flask app** specifically so it runs
natively on cPanel's "Setup Python App" feature (Phusion Passenger) --
no ASGI server, no extra bridge needed.

**Shared folder convention:** every piece (subdomain Document Root,
Python App's Application Root, Git repo's Repository Path) points at the
*same* folder: `/home/<user>/repositories/gymtrack`. Keeping these three
identical is required -- but as we learned the hard way, identical config
*values* don't always mean the underlying server is actually wired up
correctly (see the gotcha callout below). That's why the order below
matters, and why each step ends with a quick verification before moving on.

## Known gotcha (read this first)
If you ever tear down and rebuild this whole setup, cPanel/LiteSpeed can
get into a state where the subdomain's config *looks* 100% correct in
every UI page (Document Root, Application Root, Git Repository Path all
agree, `.htaccess` has valid `PassengerAppRoot`/`PassengerPython`
directives) -- yet the site returns LiteSpeed's generic 404 for
*everything*, including a plain static `.txt` file, regardless of whether
the Python App is started or stopped. This points to the server-side
vhost registration silently failing, most likely because the target
folder already had files in it (from a prior Git clone) at the moment the
subdomain was created. The fix is a full teardown + rebuild **in the
order below**, verifying the vhost works with a plain static file
*before* layering Passenger/Git on top -- that isolates which piece is
actually broken instead of debugging a fully-built mystery 404 again.

## Step 1 -- Create the subdomain FIRST, alone
1. Make sure `/home/<user>/repositories/gymtrack` is completely empty (or
   doesn't exist yet) before starting -- delete it via File Manager if
   it's left over from a previous attempt.
2. cPanel -> **Domains** -> **Create A New Domain** -> subdomain
   `gymtrack` on your root domain.
3. Set **Document Root** explicitly to `repositories/gymtrack` (override
   cPanel's default `public_html/gymtrack` suggestion).
4. **Checkpoint -- verify before continuing:** in File Manager, create a
   throwaway `test.txt` inside `repositories/gymtrack`, then visit
   `https://gymtrack.yourdomain.com/test.txt` in a browser. You must see
   the file's contents, not a 404, before moving to Step 2. If this
   fails, stop here -- the vhost itself is broken and no amount of Python
   App or Git config will fix it (this is the "shared hosting ticket"
   territory, see Troubleshooting below). Delete `test.txt` once confirmed.

## Step 2 -- Create the Python App, pointing at the same folder
1. cPanel -> **Software -> Setup Python App** -> **Create Application**.
2. Python version: pick the highest 3.x available (check what's offered;
   anything 3.9+ works). Note the exact version string shown -- you'll
   need it for `scripts/cpanel-deploy.sh` later.
3. **Application root**: `repositories/gymtrack` -- must exactly match
   Step 1's Document Root.
4. **Application URL**: the same subdomain from Step 1.
5. **Application startup file**: `passenger_wsgi.py`
6. **Application Entry point**: `application`
7. Click **Create**.
8. **Checkpoint:** refresh `https://gymtrack.yourdomain.com/` -- you
   should see cPanel's default "it works" placeholder page (no
   `passenger_wsgi.py` of ours exists yet), not a 404. If you get a 404
   here, the Python App creation itself didn't wire up correctly --
   don't proceed to Git yet.

## Step 3 -- Git Version Control, pointing at the same folder
**`main` is the deploy branch.** Active day-to-day development happens on
`dev` -- `main` only moves forward when you deliberately merge a release
cut into it.

1. cPanel -> **Git Version Control** -> **Create**
2. **Clone URL**: `https://github.com/hermanno18/GymTrack.git`
3. **Repository Path**: `/home/<user>/repositories/gymtrack` -- cPanel
   may try to suggest this exact path by default anyway, but type it
   explicitly and double check it matches Steps 1 & 2 -- don't just
   accept whatever's pre-filled without looking.
4. **Branch**: `main`
5. Click **Create**.
6. **Checkpoint:** refresh the subdomain again -- you should now get
   either a working app or a Flask-level error (proof Passenger is at
   least executing *our* `passenger_wsgi.py` now), not LiteSpeed's
   generic 404. Finish Steps 4-7 before expecting a fully working app.

## Step 4 -- Fill in `scripts/cpanel-deploy.sh` once
Open `scripts/cpanel-deploy.sh` (via File Manager's Code Editor is fine,
no terminal needed) and confirm these two values match what Steps 1-2
actually gave you:
```bash
CPANEL_USERNAME="<your actual cPanel username>"
PYTHON_VERSION="<exact version folder from Step 2, e.g. 3.10>"
```
Commit and push that change once if you edit it directly on the server --
it's account-specific config, not a secret, so it's fine to commit.
`.cpanel.yml` itself never needs editing; it just calls this script.

## Step 5 -- Deploy
1. cPanel -> **Git Version Control** -> your repo -> **Manage**
2. Click **Update from Remote** (pulls the latest commit)
3. Click **Deploy HEAD Commit**
4. Check the **Pull or Deploy** log on that same page -- confirm
   `pip install` and the restart-touch actually ran without errors,
   don't just trust that the UI says "deployed."

### Every deploy after that
Just repeat Step 5 (Update from Remote -> Deploy HEAD Commit) -- the
`.cpanel.yml` task activates the venv, runs
`pip install -r requirements.txt`, and touches `tmp/restart.txt` so
Passenger picks up the new code immediately.

### If something goes wrong with the automated deploy
Fall back to doing it by hand via cPanel -> **Terminal** (if you have
terminal access -- if not, see Troubleshooting below):
```bash
source /home/<user>/virtualenv/repositories/gymtrack/<python-version>/bin/activate
cd /home/<user>/repositories/gymtrack
git pull
pip install -r requirements.txt
touch tmp/restart.txt
```

## Step 6 -- Set environment variables
In the cPanel Python App UI, add:
- `SECRET_KEY` -- a long random string (used to sign session cookies)
- `SESSION_COOKIE_SECURE` -- set to `true` once HTTPS/AutoSSL is
  confirmed working on the domain (makes the session cookie HTTPS-only).
  **Leave unset/false until then** -- a Secure cookie sent over plain
  HTTP is silently dropped by the browser, which breaks login.

To enable the "forgot password" email flow, also add (optional --
without these, reset links are logged to the app's log file instead of
being emailed, which still works for testing but not for real users):
- `SMTP_HOST` -- e.g. `mail.yourdomain.com` (your cPanel mailbox's SMTP server)
- `SMTP_PORT` -- `587` for STARTTLS (typical) or `465` for implicit SSL
- `SMTP_USERNAME` -- full mailbox address, e.g. `noreply@yourdomain.com`
- `SMTP_PASSWORD` -- that mailbox's password
- `SMTP_FROM_EMAIL` -- optional, defaults to `SMTP_USERNAME` if unset
- `SMTP_USE_SSL` -- optional, set to `true` only if using port 465

## Step 7 -- SSL
cPanel -> **SSL/TLS Status** -> run AutoSSL for the subdomain (usually
free). Don't flip `SESSION_COOKIE_SECURE` to `true` (Step 6) until this
is confirmed working.

## Step 8 -- Restart (first time only)
Back on the Setup Python App page, click **Restart** once, after the
initial Git pull + `pip install` + env vars are all in place. Visit your
subdomain to confirm it's live. From here on, every future deploy's
restart is handled automatically by `scripts/cpanel-deploy.sh` (Step 5) --
you shouldn't need to click Restart manually again.

## Troubleshooting: LiteSpeed 404 that won't go away
If you hit the exact symptom described in the gotcha above (404 for
everything, static files included, app started or stopped makes no
difference) and the Step 1 checkpoint fails even on a fresh empty folder:
this is a server-side vhost issue outside of what cPanel's own UI can
fix. Open a support ticket with your host with this summary:

> Subdomain `gymtrack.yourdomain.com` returns LiteSpeed's generic 404 for
> *all* requests, including a static file placed directly in its
> Document Root. Document Root, Application Root, and Git repository
> path all correctly point to the same folder per cPanel's UI. Suspect
> the LiteSpeed vhost config for this domain is stale/not regenerated --
> can you rebuild the vhost config for this domain?

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
  Step 5 -- it reinstalls dependencies every time anyway).
