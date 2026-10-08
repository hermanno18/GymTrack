# Deploying GymTrack (Nuxt) on WHC (cPanel / Passenger)

GymTrack is built with Nuxt 4's `node-server` Nitro preset -- a plain,
self-contained Node HTTP server with no external runtime dependencies
(no separate database server, no Redis, no reverse-proxy requirement).
This maps directly onto cPanel's **"Setup Node.js App"** feature
(Phusion Passenger), the same way the old Flask app used "Setup Python App".

## 0. Before you start: build it once, locally, and run it as production
Don't skip this. `nuxt dev` silently papers over at least one thing that
breaks in a real production run (see the big warning in Step 4). Confirm
locally first:
```bash
npm install
npm run build
NUXT_SESSION_PASSWORD=some-random-32-plus-char-string npm start
```
Visit `http://localhost:3000` and actually log in. If that works, you're
clear to deploy the exact same code.

## 1. Create the Node.js App in cPanel
1. cPanel → **Software → Setup Node.js App** → **Create Application**.
2. Node.js version: pick the highest available that satisfies `.nvmrc`
   (currently Node **22.21.0+** -- check what's offered; anything 22.x works).
3. Application mode: **Production**.
4. Application root: e.g. `gymtrack` (a folder under your home dir). This
   becomes your app's **working directory** at runtime -- important, see
   Step 5's note on the SQLite path and migrations folder.
5. Application URL: your subdomain (e.g. `gymtrack.yourdomain.com`).
6. Application startup file: `.output/server/index.mjs`
   (this only exists *after* you've run `npm run build` -- Step 3).
7. Click **Create**. cPanel will show you an "Enter to the virtual
   environment" command -- note the path, you'll use it in Step 3.

## 2. Get the code onto the server (one-time Git Version Control setup)
Same convention as the old Flask app: **`main` is the deploy branch**,
active development happens on other branches, `main` only moves forward
when you deliberately merge a release cut into it.

1. cPanel → **Git Version Control** → **Create**
2. **Clone URL**: `https://github.com/hermanno18/GymTrack.git`
3. **Repository Path**: `/home/<user>/gymtrack` (must match the
   Application root from Step 1 exactly)
4. **Branch**: `main`
5. Click **Create**

The whole repo gets cloned, including `legacy-flask/` -- that's fine,
it's inert (not referenced by anything at runtime) until you're ready to
delete it for good.

## 3. Install dependencies and build
Open cPanel → **Terminal** (or SSH in), then:
```bash
# Activate the Node virtual environment cPanel created in Step 1
source /home/<user>/nodevenv/gymtrack/22/bin/activate   # path shown on the app's page

cd /home/<user>/gymtrack
npm install
npm run build
```
`npm install` compiles/fetches `better-sqlite3`'s native addon for
*this* server's exact Node version and OS -- that's precisely why this
needs to run on the server itself, not be copied over from your laptop.
If it fails trying to compile from source (no `make`/`python`/`gcc` on a
constrained shared host), check whether `better-sqlite3` shipped a
prebuilt binary for this Node version/platform first; if not, you'll
need to ask your host to enable build tools for this account.

`npm run build` produces `.output/` (the Nitro server bundle +
pre-rendered client assets) -- this is a regular build step that must
re-run on every deploy, same spirit as the Flask app's `pip install`.

## 4. Set environment variables -- READ THIS, it's the one gotcha that
   actually breaks things
**`nuxt dev` auto-loads your local `.env` file. The built production
server (`.output/server/index.mjs`, i.e. what cPanel actually runs)
does NOT.** It only reads real OS/process environment variables. If you
skip this step the app will boot (no crash, no obvious error at
startup) but every single request that touches a session --
login, signup, every logged-in page -- will throw a 500
(`H3Error: Empty password`, from nuxt-auth-utils failing to seal the
session cookie with an empty secret). This is exactly the kind of bug
that looks fine in a quick smoke test of the homepage and then breaks
the instant someone tries to log in.

In the cPanel "Setup Node.js App" UI, scroll to **Environment
Variables** and add:
- `NUXT_SESSION_PASSWORD` — a long random string (32+ chars), used to
  sign/encrypt session cookies **and** password-reset tokens. Generate
  one with `openssl rand -hex 32` or similar. Changing this later
  invalidates all existing sessions and any in-flight reset links --
  that's expected, not a bug.
- `DATABASE_PATH` — optional, defaults to `./data/gymtrack.db` (relative
  to the Application root). Leave unset unless you have a reason to
  move it.

To enable the "forgot password" email flow, also add (optional --
without these, reset links are logged to the app's log instead of being
emailed, which still works for testing but not for real users):
- `SMTP_HOST` — e.g. `mail.yourdomain.com` (your cPanel mailbox's SMTP server)
- `SMTP_PORT` — `587` for STARTTLS (typical) or `465` for implicit SSL
- `SMTP_USERNAME` — full mailbox address, e.g. `noreply@yourdomain.com`
- `SMTP_PASSWORD` — that mailbox's password
- `SMTP_FROM_EMAIL` — optional, defaults to `SMTP_USERNAME` if unset
- `SMTP_USE_SSL` — optional, set to `true` only if using port 465

After adding/changing env vars, click **Restart** on the app's page for
them to take effect.

## 5. Point the subdomain + SSL
1. cPanel → **Domains** → create the subdomain if you haven't already,
   pointing at the same application root.
2. cPanel → **SSL/TLS Status** → run AutoSSL for the subdomain.
3. `nuxt-auth-utils` automatically marks the session cookie `Secure`
   once it detects production mode -- no env var needed for this (unlike
   the old Flask app's `SESSION_COOKIE_SECURE` toggle). Just make sure
   AutoSSL is actually working before real users log in, or the cookie
   won't be sent over plain HTTP.

## 6. First boot
Back on the Setup Node.js App page, click **Restart**. Visit your
subdomain and confirm:
- The homepage loads.
- You can sign up / log in (this is the step Step 4's gotcha breaks if
  missed -- don't skip testing this specific thing).
- The terminal/app log shows `[db] migrations applied` on startup --
  that's the SQLite schema being created automatically, no manual
  migration step needed, ever.

## Every deploy after the first
```bash
# cPanel -> Git Version Control -> your repo -> Manage
#   1. "Update from Remote" (pulls latest commit on main)
#   2. "Deploy HEAD Commit"

# Then back in Terminal:
source /home/<user>/nodevenv/gymtrack/22/bin/activate
cd /home/<user>/gymtrack
npm install    # only does real work if dependencies changed
npm run build  # always re-run -- picks up every code change
```
Then click **Restart** on the Setup Node.js App page. There's no
`.cpanel.yml` one-click automation for this yet (the Flask app's
version doesn't translate directly -- Node builds are slower and
`better-sqlite3`'s native compile step makes "restart automatically
after every git push" riskier to fully automate blind). Worth revisiting
once the app's deploy cadence picks up.

## Notes
- The SQLite DB lives at `data/gymtrack.db` under the Application root
  by default -- outside any statically-served directory, and **must
  survive deploys**. `npm install`/`npm run build` never touch it, but
  don't `git clean -fdx` or similar on this server without excluding
  `data/`.
- Migrations run automatically on every server start (see
  `server/plugins/migrate.ts`) by reading `server/database/migrations/`
  **relative to the process's working directory** -- this is why the
  Application root must be the full repo checkout (not just `.output/`
  copied somewhere else). Deploying only the build output without the
  rest of the repo will boot fine but silently skip all migrations.
- `legacy-flask/` ships along for the ride in every checkout. It's
  dead weight at this point (nothing in the Nuxt app reads it) --
  safe to delete from the server once you've confirmed the Nuxt
  version is solid, just don't delete it from git history/the `main`
  branch without a deliberate decision to do so.
- Known rough edge, not a deploy blocker: `nuxt typecheck` currently
  fails locally due to a `vue-tsc`/TypeScript version mismatch in this
  toolchain, unrelated to app code. Every feature in this app has been
  verified by actually running it (dev server + a full production
  build + `npm start`), not by typecheck, so this doesn't affect
  runtime correctness -- it just means a real type-level check is
  pending a tooling fix.
