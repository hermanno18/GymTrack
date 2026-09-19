"""
GymTrack application factory.

Kept intentionally small (Zen of Python: flat is better than nested) --
all the real logic lives in per-feature blueprint modules.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "error"
csrf = CSRFProtect()


def create_app(test_config=None):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + os.path.join(app.instance_path, "gymtrack.db"),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB cap on PDF uploads
        FUZZY_MATCH_THRESHOLD=0.85,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401  (registers models with SQLAlchemy)

    with app.app_context():
        db.create_all()
        _ensure_schema_migrations()

    _register_blueprints(app)
    _register_user_loader()
    _register_template_filters(app)

    return app


def _register_blueprints(app):
    from .auth import auth_bp
    from .settings import settings_bp
    from .programs import programs_bp
    from .builder import builder_bp
    from .workouts import workouts_bp
    from .guided import guided_bp
    from .dashboard import dashboard_bp

    for bp in (auth_bp, settings_bp, programs_bp, builder_bp, workouts_bp, guided_bp, dashboard_bp):
        app.register_blueprint(bp)


def _register_user_loader():
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return db.session.get(User, int(user_id))


def _register_template_filters(app):
    from .utils import (
        kg_to_display, km_to_display, format_seconds_to_duration,
        format_full_date, format_short_date, format_time_12h, format_full_datetime,
    )

    app.jinja_env.filters["display_weight"] = kg_to_display
    app.jinja_env.filters["display_distance"] = km_to_display
    app.jinja_env.filters["display_duration"] = format_seconds_to_duration
    app.jinja_env.filters["full_date"] = format_full_date
    app.jinja_env.filters["short_date"] = format_short_date
    app.jinja_env.filters["time_12h"] = format_time_12h
    app.jinja_env.filters["full_datetime"] = format_full_datetime


def _ensure_schema_migrations():
    """
    Tiny ad-hoc migration safety net for SQLite.

    db.create_all() only creates missing *tables*, it never alters
    existing ones -- so a column added to a model after someone already
    has a local gymtrack.db would otherwise cause 'no such column'
    errors. This is deliberately lightweight (no Alembic) since the app
    is small and single-database; add real migrations if that changes.
    """
    from sqlalchemy import text

    columns_to_ensure = [
        ("exercise", "target_duration_seconds", "INTEGER"),
        ("workout_log", "actual_duration_seconds", "INTEGER"),
        ("workout_session", "start_time", "VARCHAR(5)"),
        ("workout_session", "end_time", "VARCHAR(5)"),
        ("workout_log", "started_at", "VARCHAR(8)"),
        ("workout_log", "work_seconds", "INTEGER"),
        ("workout_log", "rest_seconds", "INTEGER"),
    ]
    with db.engine.connect() as conn:
        for table, column, col_type in columns_to_ensure:
            existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))]
            if existing and column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
