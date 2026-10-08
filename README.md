# GymTrack

A lightweight, multi-user workout tracker. Upload your coach's PDF training
program (or build one by hand), log your actual sets/reps/weight/distance
per session, and watch your progression over time.

> **Status: Nuxt rewrite complete, feature-parity with the original Flask
> app reached.** The original Flask implementation is preserved under
> [`legacy-flask/`](./legacy-flask/) for reference; it's no longer the
> deployed version. See `legacy-flask/README.md` for its own history.

## Stack
- Nuxt 4 (SSR, Nitro `node-server` preset) — deployed via cPanel's
  "Setup Node.js App" (Passenger), same pattern as the old Flask app used
  for Python. See [`DEPLOY.md`](./DEPLOY.md).
- Drizzle ORM + `better-sqlite3` (single-file DB, same storage model as before)
- `nuxt-auth-utils` for sessions (`SameSite=Lax` + `Secure`-in-production
  cookies -- this is the app's CSRF defense; no separate CSRF module needed)
- `@nuxtjs/tailwindcss`
- `chart.js` for progression charts
- `unpdf` for PDF text extraction, feeding a hand-ported regex parser
  (`server/utils/pdfParser.ts`) matching the original `pdf_parser.py`
- `nodemailer` for password-reset emails (falls back to logging the
  reset link when SMTP isn't configured -- see `DEPLOY.md`)

## Feature set
Full parity with the original Flask app:
- Auth + multi-user data isolation, password reset via email
- Manual program builder (Program → Day → Exercise) with fuzzy
  "Did you mean X?" duplicate-name catching
- PDF program upload with auto-extraction, falling back cleanly to the
  manual builder when a PDF can't be parsed
- Guided Session mode: work/rest countdown timer, personal-best targets,
  resume-after-refresh, screen wake lock
- Workout logging (guided, manual quick-log, and free-form/ad-hoc)
- Animated "story" timeline for every logged session
- Progression charts per exercise (Chart.js)
- Per-user unit preferences (kg/lb, km/mi), settings page (units/email/password)

No data migration was needed going into this rewrite -- the prior
deployment had no real user data to carry over, so it started fresh.

## Local development

Requires **Node >= 22.21.0** (see `.nvmrc`). Nuxt is pinned to `4.5.2`
rather than `latest` — `4.6.0` (published Oct 2026) has a dev-server
regression (`Either manifest or precomputed data must be provided` on
every request); revisit the pin once a patch release fixes it upstream.

```bash
npm install
cp .env.example .env   # then set NUXT_SESSION_PASSWORD to anything 32+ chars
npm run dev
```

Opens at http://localhost:3000.

To test an actual production build locally (recommended before every
deploy -- see `DEPLOY.md` for why):
```bash
npm run build
NUXT_SESSION_PASSWORD=... npm start
```

## Core concepts
- **Program → Day → Exercise → (target sets/reps/weight/distance)**
  Matches a typical "Day 1 / Day 2..." coach program.
- **Exercise history carries over automatically** across programs when the
  exercise name matches (case/whitespace-insensitive, fuzzy-matched). A
  "Did you mean X?" prompt catches near-duplicates while you're typing.
- **PDF upload is best-effort.** If it can't be parsed cleanly, you land
  straight in the same manual program builder used for from-scratch
  programs -- no dead end.
- **Units are a per-user setting** (kg/lb, km/mi). Everything is stored
  internally in kg/km and converted only for display/input.
- **Guided Session is the primary logging path** for a program day
  (timer-driven, PR-aware); manual quick-log and free-form logging are
  always available as a fallback via a small edit icon.

## Deployment
See [`DEPLOY.md`](./DEPLOY.md) for the full cPanel/Passenger walkthrough,
including one non-obvious gotcha around environment variables that will
otherwise break login in production. `legacy-flask/DEPLOY.md` is kept for
historical reference only.

## Known rough edges
- `nuxt typecheck` currently fails locally due to a `vue-tsc`/TypeScript
  version mismatch in the toolchain, unrelated to application code.
  Every feature has instead been verified by actually running it (dev
  server + a real production build), not by static typecheck.
