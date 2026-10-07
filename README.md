# GymTrack

A lightweight, multi-user workout tracker. Upload your coach's PDF training
program (or build one by hand), log your actual sets/reps/weight/distance
per session, and watch your progression over time.

> **Status: mid-rewrite.** This branch (`nuxt-rewrite`) is converting the
> project from Flask to Nuxt 4. The original, fully-working Flask
> implementation is preserved under [`legacy-flask/`](./legacy-flask/) and
> stays deployed until the Nuxt version reaches feature parity. See
> `legacy-flask/README.md` for why.

## Stack (Nuxt rewrite, in progress)
- Nuxt 4 (SSR, Nitro `node-server` preset) — deployed via cPanel's
  "Setup Node.js App" (Passenger), same pattern as the old Flask app used
  for Python
- Drizzle ORM + `better-sqlite3` (single-file DB, same storage model as before)
- `nuxt-auth-utils` for sessions, `nuxt-csurf` for CSRF
- `@nuxtjs/tailwindcss`
- `vue-chartjs` (Chart.js) for progression charts
- PDF parsing: TBD in Phase 2 (`unpdf`/`pdf-parse`, replacing `pdfplumber`)

## Rewrite scope
**Phase 1 (MVP):** auth + multi-user isolation, manual program builder
(Program → Day → Exercise), workout logging.
**Phase 2:** PDF upload/parsing with manual-builder fallback, fuzzy
exercise-name matching + cross-program history carryover, progression
charts, per-user unit settings (kg/lb, km/mi), password-reset email.

No data migration needed — starting fresh (old deployment has no real
user data to carry over).

## Local development

Requires **Node >= 22.21.0** (see `.nvmrc`). Nuxt is pinned to `4.5.2`
rather than `latest` — `4.6.0` (published Oct 2026) has a dev-server
regression (`Either manifest or precomputed data must be provided` on
every request); revisit the pin once a patch release fixes it upstream.

```bash
npm install
npm run dev
```

Opens at http://localhost:3000.

## Core concepts
- **Program → Day → Exercise → (target sets/reps/weight/distance)**
  Matches a typical "Day 1 / Day 2..." coach program.
- **Exercise history carries over automatically** across programs when the
  exercise name matches (case/whitespace-insensitive). A "Did you mean X?"
  prompt catches near-duplicates while you're typing.
- **PDF upload is best-effort.** If it can't be parsed cleanly, you land
  straight in the same manual program builder used for from-scratch
  programs -- no dead end.
- **Units are a per-user setting** (kg/lb, km/mi). Everything is stored
  internally in kg/km and converted only for display/input.

## Deployment
New `DEPLOY.md` for the Nuxt/Node cPanel setup lands once Phase 1 is
deployable. Until then, see `legacy-flask/DEPLOY.md` for the Flask
version's WHC/cPanel Passenger walkthrough.
