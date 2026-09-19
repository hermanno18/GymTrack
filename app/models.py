"""
Database models.

Schema shape (matches the coach's "Day 1 / Day 2..." program format):

    User --< UserSettings (1:1)
    User --< Program --< ProgramDay --< Exercise --< WorkoutLog
    User --< WorkoutSession --< WorkoutLog

Exercise.name_normalized is the join key that lets progression history
carry over automatically when the same exercise name shows up in a new
program (see utils.normalize_name).
"""
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    settings = db.relationship(
        "UserSettings", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    programs = db.relationship("Program", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    weight_unit = db.Column(db.String(4), default="kg", nullable=False)      # 'kg' | 'lb'
    distance_unit = db.Column(db.String(4), default="km", nullable=False)    # 'km' | 'mi'


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    source_pdf_filename = db.Column(db.String(255), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)

    days = db.relationship(
        "ProgramDay", backref="program", cascade="all, delete-orphan",
        order_by="ProgramDay.order_index",
    )


class ProgramDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("program.id"), nullable=False)
    label = db.Column(db.String(120), nullable=False)  # e.g. "Day 1"
    order_index = db.Column(db.Integer, default=0)

    exercises = db.relationship(
        "Exercise", backref="program_day", cascade="all, delete-orphan",
        order_by="Exercise.order_index",
    )


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_day_id = db.Column(db.Integer, db.ForeignKey("program_day.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    name_normalized = db.Column(db.String(255), nullable=False, index=True)
    category = db.Column(db.String(50), default="strength")  # strength | cardio | other
    target_sets = db.Column(db.Integer, nullable=True)
    target_reps = db.Column(db.Integer, nullable=True)
    target_weight_kg = db.Column(db.Float, nullable=True)
    target_distance_km = db.Column(db.Float, nullable=True)
    target_duration_seconds = db.Column(db.Integer, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    notes = db.Column(db.String(500), nullable=True)

    logs = db.relationship("WorkoutLog", backref="exercise", cascade="all, delete-orphan")


class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    program_day_id = db.Column(db.Integer, db.ForeignKey("program_day.id"), nullable=True)
    date = db.Column(db.Date, default=date.today)
    start_time = db.Column(db.String(5), nullable=True)  # "HH:MM", 24h
    end_time = db.Column(db.String(5), nullable=True)    # "HH:MM", 24h
    notes = db.Column(db.String(500), nullable=True)

    program_day = db.relationship("ProgramDay")
    logs = db.relationship("WorkoutLog", backref="session", cascade="all, delete-orphan")


class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("workout_session.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"), nullable=False)
    actual_sets = db.Column(db.Integer, nullable=True)
    actual_reps = db.Column(db.Integer, nullable=True)
    actual_weight_kg = db.Column(db.Float, nullable=True)
    actual_distance_km = db.Column(db.Float, nullable=True)
    actual_duration_seconds = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(500), nullable=True)
