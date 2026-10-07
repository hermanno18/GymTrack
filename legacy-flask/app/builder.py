"""
Program builder: add/edit/delete Days and Exercises. This is the single
screen used both for reviewing PDF-extracted programs AND for building a
program fully from scratch -- one UI, two entry points (see programs.py).

Day/exercise add + edit use plain form POST + redirect (simple, infrequent
actions, no need to over-engineer). Deletes and the duplicate-name
suggestion lookup use HTMX so the page doesn't jump around for those.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app,
)
from flask_login import login_required, current_user

from . import db
from .models import Program, ProgramDay, Exercise
from .utils import (
    normalize_name, find_similar_exercise, display_to_kg, display_to_km,
    parse_duration_to_seconds, format_seconds_to_duration,
)

builder_bp = Blueprint("builder", __name__)


def _get_owned_program(program_id):
    return Program.query.filter_by(id=program_id, user_id=current_user.id).first_or_404()


def _get_owned_day(day_id):
    return (
        ProgramDay.query.join(Program)
        .filter(ProgramDay.id == day_id, Program.user_id == current_user.id)
        .first_or_404()
    )


def _get_owned_exercise(exercise_id):
    return Exercise.query.filter_by(id=exercise_id, user_id=current_user.id).first_or_404()


@builder_bp.route("/programs/<int:program_id>/builder")
@login_required
def edit_program(program_id):
    program = _get_owned_program(program_id)
    return render_template(
        "programs/builder.html", program=program, settings=current_user.settings
    )


@builder_bp.route("/programs/<int:program_id>/days", methods=["POST"])
@login_required
def add_day(program_id):
    program = _get_owned_program(program_id)
    label = request.form.get("label", "").strip() or f"Day {len(program.days) + 1}"
    next_order = len(program.days)
    db.session.add(ProgramDay(program_id=program.id, label=label, order_index=next_order))
    db.session.commit()
    return redirect(url_for("builder.edit_program", program_id=program.id))


@builder_bp.route("/days/<int:day_id>/delete", methods=["POST"])
@login_required
def delete_day(day_id):
    day = _get_owned_day(day_id)
    db.session.delete(day)
    db.session.commit()
    return ""  # HTMX swap removes the element client-side


@builder_bp.route("/days/<int:day_id>/exercises", methods=["POST"])
@login_required
def add_exercise(day_id):
    day = _get_owned_day(day_id)
    unit_settings = current_user.settings

    name = request.form.get("name", "").strip()
    if not name:
        flash("Exercise name is required.", "error")
        return redirect(url_for("builder.edit_program", program_id=day.program_id))

    next_order = len(day.exercises)
    db.session.add(Exercise(
        program_day_id=day.id,
        user_id=current_user.id,
        name=name,
        name_normalized=normalize_name(name),
        category=request.form.get("category", "strength"),
        target_sets=_to_int(request.form.get("sets")),
        target_reps=_to_int(request.form.get("reps")),
        target_weight_kg=display_to_kg(request.form.get("weight"), unit_settings.weight_unit),
        target_distance_km=display_to_km(request.form.get("distance"), unit_settings.distance_unit),
        target_duration_seconds=_to_duration(request.form.get("duration")),
        order_index=next_order,
        notes=request.form.get("notes", "").strip() or None,
    ))
    db.session.commit()
    return redirect(url_for("builder.edit_program", program_id=day.program_id))


@builder_bp.route("/exercises/<int:exercise_id>/delete", methods=["POST"])
@login_required
def delete_exercise(exercise_id):
    exercise = _get_owned_exercise(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    return ""  # HTMX swap removes the element client-side


@builder_bp.route("/exercises/<int:exercise_id>/edit", methods=["GET", "POST"])
@login_required
def edit_exercise(exercise_id):
    exercise = _get_owned_exercise(exercise_id)
    unit_settings = current_user.settings

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Exercise name is required.", "error")
            return redirect(url_for("builder.edit_exercise", exercise_id=exercise.id))

        exercise.name = name
        exercise.name_normalized = normalize_name(name)
        exercise.category = request.form.get("category", "strength")
        exercise.target_sets = _to_int(request.form.get("sets"))
        exercise.target_reps = _to_int(request.form.get("reps"))
        exercise.target_weight_kg = display_to_kg(request.form.get("weight"), unit_settings.weight_unit)
        exercise.target_distance_km = display_to_km(request.form.get("distance"), unit_settings.distance_unit)
        exercise.target_duration_seconds = _to_duration(request.form.get("duration"))
        exercise.notes = request.form.get("notes", "").strip() or None
        db.session.commit()
        flash("Exercise updated.", "success")
        return redirect(url_for("builder.edit_program", program_id=exercise.program_day.program_id))

    return render_template(
        "programs/edit_exercise.html", exercise=exercise, settings=unit_settings,
        duration_display=format_seconds_to_duration(exercise.target_duration_seconds),
    )


@builder_bp.route("/exercises/suggest")
@login_required
def suggest_exercise_name():
    """HTMX live lookup powering the 'Did you mean X?' duplicate prompt."""
    typed_name = request.args.get("name", "").strip()
    exclude_id = request.args.get("exclude_id", type=int)

    if not typed_name:
        return ""

    query = db.session.query(Exercise.id, Exercise.name, Exercise.name_normalized).filter(
        Exercise.user_id == current_user.id
    )
    if exclude_id:
        query = query.filter(Exercise.id != exclude_id)

    seen = {}
    for ex_id, ex_name, ex_norm in query.all():
        seen.setdefault(ex_norm, (ex_id, ex_name, ex_norm))

    match = find_similar_exercise(
        typed_name, seen.values(), current_app.config["FUZZY_MATCH_THRESHOLD"]
    )
    if not match or match["exact"]:
        return ""  # no suggestion needed for an exact match or no match

    return render_template("programs/_suggestion.html", match=match)


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
