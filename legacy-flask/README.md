# GymTrack (Flask) — Archived

This is the original Flask/SQLite/HTMX implementation of GymTrack, kept
here for reference while the project is rewritten in Nuxt 4 (see the root
`README.md` for why and the rewrite plan).

Nothing in this folder is deployed or maintained going forward. If you
need to run it:

```bash
cd legacy-flask
uv venv
.venv\Scripts\activate        # Windows
uv pip install -r requirements.txt
python run.py
```

See `DEPLOY.md` in this folder for the original WHC/cPanel Passenger
deployment walkthrough (the LiteSpeed-404 gotcha documented there is what
prompted re-evaluating the stack in the first place).
