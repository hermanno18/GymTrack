# GymTrack

A lightweight, multi-user workout tracker. Upload your coach's PDF training
program (or build one by hand), log your actual sets/reps/weight/distance
per session, and watch your progression over time.

## Stack
- Flask (WSGI -- deliberately, so it runs cleanly on cPanel/Passenger shared hosting)
- SQLite (single-file, standalone DB, lives in `instance/gymtrack.db`)
- HTMX + Tailwind (CDN) for a snappy, no-build-step frontend
- Chart.js for progression charts
- pdfplumber for PDF text extraction

## Local development

```bash
uv venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
uv pip install -r requirements.txt
python run.py
```

Opens automatically at http://127.0.0.1:5000. The SQLite DB and any
uploaded PDFs are stored under `instance/` (auto-created, git-ignored).

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

## Testing

```bash
uv pip install -r requirements-dev.txt
pytest
```

47 tests covering: unit conversion & fuzzy-name matching, the PDF-text
parser, auth + multi-user data isolation, the program builder (days/
exercises/duplicate suggestions), PDF upload fallback paths, workout
logging, cross-program history carryover, and CSRF protection. Tests are
grouped one file per feature area under `tests/`.

## Deployment
See `DEPLOY.md` for the WHC/cPanel Passenger deployment walkthrough.
