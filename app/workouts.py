"""
Workout logging + progression views.

Two ways to log a session:
  - against a specific ProgramDay (pre-fills that day's planned exercises)
  - fully free-form / ad-hoc (no plan at all)

Either way, "extra" exercises typed in by name are matched against the
user's existing exercises via name_normalized (find-or-create), which is
exactly what makes progression history carry over automatically.
"""
from datetime import date as date_cls

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db
from .models import Program, ProgramDay, Exercise, WorkoutSession, WorkoutLog
from .utils import (
    normalize_name, display_to_kg, display_to_km, kg_to_display, km_to_display,
    parse_duration_to_seconds, format_short_date,
)

workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")


@workouts_bp.route("/log")
@login_required
def log_picker():
    programs = (
        Program.query.filter_by(user_id=current_user.id)
        .order_by(Program.created_at.desc())
        .all()
    )
    return render_template("workouts/picker.html", programs=programs)


@workouts_bp.route("/log/adhoc", methods=["GET", "POST"])
@login_required
def log_adhoc():
    if request.method == "POST":
        _save_session(day=None)
        return redirect(url_for("dashboard.home"))
    return render_template(
        "workouts/log.html", day=None, settings=current_user.settings,
        today=date_cls.today().isoformat(),
    )


@workouts_bp.route("/log/<int:day_id>", methods=["GET", "POST"])
@login_required
def log_day(day_id):
    day = (
        ProgramDay.query.join(Program)
        .filter(ProgramDay.id == day_id, Program.user_id == current_user.id)
        .first_or_404()
    )
    if request.method == "POST":
        _save_session(day=day)
        return redirect(url_for("dashboard.home"))
    return render_template(
        "workouts/log.html", day=day, settings=current_user.settings,
        today=date_cls.today().isoformat(),
    )


def _save_session(day):
    unit_settings = current_user.settings
    session_date = request.form.get("date") or date_cls.today().isoformat()
    workout_session = WorkoutSession(
        user_id=current_user.id,
        program_day_id=day.id if day else None,
        date=date_cls.fromisoformat(session_date),
        start_time=request.form.get("start_time") or None,
        end_time=request.form.get("end_time") or None,
        notes=request.form.get("session_notes", "").strip() or None,
    )
    db.session.add(workout_session)
    db.session.flush()

    if day:
        for exercise in day.exercises:
            _log_planned_exercise(workout_session, exercise, unit_settings)

    _log_extra_exercises(workout_session, unit_settings)

    db.session.commit()
    flash("Workout logged. Nice work!", "success")


def _log_planned_exercise(workout_session, exercise, unit_settings):
    prefix = f"ex_{exercise.id}"
    sets = _to_int(request.form.get(f"{prefix}_sets"))
    reps = _to_int(request.form.get(f"{prefix}_reps"))
    weight = request.form.get(f"{prefix}_weight")
    distance = request.form.get(f"{prefix}_distance")
    duration = _to_duration(request.form.get(f"{prefix}_duration"))

    if not any([sets, reps, weight, distance, duration]):
        return  # skipped this exercise today, nothing to log

    db.session.add(WorkoutLog(
        session_id=workout_session.id,
        exercise_id=exercise.id,
        actual_sets=sets,
        actual_reps=reps,
        actual_weight_kg=display_to_kg(weight, unit_settings.weight_unit),
        actual_distance_km=display_to_km(distance, unit_settings.distance_unit),
        actual_duration_seconds=duration,
    ))


def _log_extra_exercises(workout_session, unit_settings):
    names = request.form.getlist("adhoc_name")
    sets_list = request.form.getlist("adhoc_sets")
    reps_list = request.form.getlist("adhoc_reps")
    weight_list = request.form.getlist("adhoc_weight")
    distance_list = request.form.getlist("adhoc_distance")
    duration_list = request.form.getlist("adhoc_duration")

    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        exercise = _find_or_create_exercise(name)
        db.session.add(WorkoutLog(
            session_id=workout_session.id,
            exercise_id=exercise.id,
            actual_sets=_to_int(_at(sets_list, i)),
            actual_reps=_to_int(_at(reps_list, i)),
            actual_weight_kg=display_to_kg(_at(weight_list, i), unit_settings.weight_unit),
            actual_distance_km=display_to_km(_at(distance_list, i), unit_settings.distance_unit),
            actual_duration_seconds=_to_duration(_at(duration_list, i)),
        ))


def _find_or_create_exercise(name):
    name_norm = normalize_name(name)
    existing = Exercise.query.filter_by(
        user_id=current_user.id, name_normalized=name_norm
    ).first()
    if existing:
        return existing

    adhoc_day = _get_or_create_adhoc_day()
    exercise = Exercise(
        program_day_id=adhoc_day.id,
        user_id=current_user.id,
        name=name,
        name_normalized=name_norm,
        order_index=len(adhoc_day.exercises),
    )
    db.session.add(exercise)
    db.session.flush()
    return exercise


def _get_or_create_adhoc_day():
    adhoc_program = Program.query.filter_by(
        user_id=current_user.id, name="Ad-hoc Exercises"
    ).first()
    if not adhoc_program:
        adhoc_program = Program(user_id=current_user.id, name="Ad-hoc Exercises")
        db.session.add(adhoc_program)
        db.session.flush()
        db.session.add(ProgramDay(program_id=adhoc_program.id, label="Extras", order_index=0))
        db.session.flush()
    return adhoc_program.days[0]


@workouts_bp.route("/history")
@login_required
def history():
    sessions = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutSession.date.desc())
        .all()
    )
    return render_template("workouts/history.html", sessions=sessions, settings=current_user.settings)


@workouts_bp.route("/progress")
@login_required
def progress_list():
    rows = (
        db.session.query(Exercise.name, Exercise.name_normalized)
        .filter(Exercise.user_id == current_user.id)
        .distinct()
        .order_by(Exercise.name)
        .all()
    )
    seen, unique_exercises = set(), []
    for name, name_norm in rows:
        if name_norm not in seen:
            seen.add(name_norm)
            unique_exercises.append({"name": name, "name_normalized": name_norm})
    return render_template("workouts/progress_list.html", exercises=unique_exercises)


@workouts_bp.route("/progress/<name_normalized>")
@login_required
def progress_detail(name_normalized):
    unit_settings = current_user.settings
    exercise_ids = [
        row.id for row in Exercise.query.filter_by(
            user_id=current_user.id, name_normalized=name_normalized
        ).all()
    ]
    if not exercise_ids:
        flash("No history found for that exercise.", "error")
        return redirect(url_for("workouts.progress_list"))

    logs = (
        WorkoutLog.query.join(WorkoutSession)
        .filter(WorkoutLog.exercise_id.in_(exercise_ids), WorkoutSession.user_id == current_user.id)
        .order_by(WorkoutSession.date)
        .all()
    )
    display_name = db.session.get(Exercise, exercise_ids[0]).name

    weight_label = "Weight (" + unit_settings.weight_unit + ")"
    distance_label = "Distance (" + unit_settings.distance_unit + ")"
    metric_specs = [
        ("weight", weight_label, lambda log: kg_to_display(log.actual_weight_kg, unit_settings.weight_unit)),
        ("distance", distance_label, lambda log: km_to_display(log.actual_distance_km, unit_settings.distance_unit)),
        ("duration", "Time", lambda log: log.actual_duration_seconds),
        ("reps", "Reps", lambda log: log.actual_reps),
        ("sets", "Sets", lambda log: log.actual_sets),
    ]

    series = {}
    for key, label, getter in metric_specs:
        points = [
            {"date": log.session.date.isoformat(), "label": format_short_date(log.session.date), "value": getter(log)}
            for log in logs if getter(log) is not None
        ]
        if points:
            series[key] = {"label": label, "points": points}

    if not series:
        flash("No numeric data logged for this exercise yet.", "warning")
        return redirect(url_for("workouts.progress_list"))

    return render_template(
        "workouts/progress_detail.html",
        display_name=display_name,
        series=series,
        logs=logs,
        settings=unit_settings,
    )


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_duration(value):
    try:
        return parse_duration_to_seconds(value)
    except ValueError:
        return None


def _at(a_list, index):
    return a_list[index] if index < len(a_list) else None
