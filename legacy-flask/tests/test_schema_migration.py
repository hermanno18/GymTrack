"""
Regression test for the ad-hoc SQLite column-migration safety net (see
app/__init__.py::_ensure_schema_migrations). Simulates a pre-existing
database created before duration/session-time columns existed, and
confirms starting the app against it doesn't blow up and actually adds
the missing columns.
"""
import sqlite3

from app import create_app


def test_missing_columns_are_added_to_existing_database(tmp_path):
    db_path = tmp_path / "legacy.db"

    # Build the app once to get a baseline schema, then drop the newer
    # columns to simulate an "old" database from before this feature.
    create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
    })

    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE exercise RENAME TO exercise_old")
    conn.execute("""
        CREATE TABLE exercise (
            id INTEGER PRIMARY KEY, program_day_id INTEGER, user_id INTEGER,
            name VARCHAR(255), name_normalized VARCHAR(255), category VARCHAR(50),
            target_sets INTEGER, target_reps INTEGER, target_weight_kg FLOAT,
            target_distance_km FLOAT, order_index INTEGER, notes VARCHAR(500)
        )
    """)
    conn.execute("DROP TABLE exercise_old")
    conn.commit()
    columns_before = [row[1] for row in conn.execute("PRAGMA table_info(exercise)")]
    conn.close()
    assert "target_duration_seconds" not in columns_before

    # Re-creating the app against this "legacy" db should backfill the column.
    create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
    })

    conn = sqlite3.connect(db_path)
    columns_after = [row[1] for row in conn.execute("PRAGMA table_info(exercise)")]
    conn.close()
    assert "target_duration_seconds" in columns_after
