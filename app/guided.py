"""
Guided Session mode: a phone-first, timer-driven way to work through a
program day exercise by exercise -- start an exercise, tap "done" to
start resting, tap "continue" to move to the next one. Fully additive:
the existing manual /workouts/log flow is untouched, this just gives
another way to arrive at the same WorkoutSession/WorkoutLog tables.

The entire live-timer experience runs client-side (see
templates/guided/session.html) -- the server only renders the initial
exercise list and accepts one final JSON POST with everything that
happened, which keeps this compatible with plain WSGI hosting (no
websockets, no background jobs, no server-side session state to manage
across requests).
"""
from datetime import date as date_cls

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user

from . import db
from .models import Program, ProgramDay, Exercise, WorkoutSession, WorkoutLog
from .utils import display_to_kg, display_to_km, kg_to_display, km_to_display, format_seconds_to_duration

guided_bp = Blueprint("guided", __name__, url_prefix="/guided")


def _get_owned_day(day_id):
    return (
        ProgramDay.query.join(Program)
        .filter(ProgramDay.id == day_id, Program.user_id == current_user.id)
        .first_or_404()
    )


@guided_bp.route("/<int:day_id>")
@login_required
def session_start(day_id):
    day = _get_owned_day(day_id)
    if not day.exercises:
        flash("This day has no exercises yet -- add some in the program builder first.", "error")
        return redirect(url_for("builder.edit_program", program_id=day.program_id))

    unit_settings = current_user.settings
    exercises_payload = [
        {
            "id": ex.id,
            "name": ex.name,
            "target_sets": ex.target_sets,
            "target_reps": ex.target_reps,
            "target_weight_display": kg_to_display(ex.target_weight_kg, unit_settings.weight_unit),
            "target_distance_display": km_to_display(ex.target_distance_km, unit_settings.distance_unit),
            "target_duration_display": format_seconds_to_duration(ex.target_duration_seconds),
            "is_timed": ex.target_duration_seconds is not None,
            "notes": ex.notes,
        }
        for ex in day.exercises
    ]

    return render_template(
        "guided/session.html",
        day=day,
        exercises_json=exercises_payload,
        settings=unit_settings,
    )


@guided_bp.route("/<int:day_id>/finish", methods=["POST"])
@login_required
def session_finish(day_id):
    day = _get_owned_day(day_id)
    unit_settings = current_user.settings
    payload = request.get_json(silent=True) or {}
    results = payload.get("results", [])

    workout_session = WorkoutSession(
        user_id=current_user.id,
        program_day_id=day.id,
        date=date_cls.today(),
        start_time=payload.get("start_time"),
        end_time=payload.get("end_time"),
        notes="Guided session",
    )
    db.session.add(workout_session)
    db.session.flush()

    for entry in results:
        exercise = Exercise.query.filter_by(id=entry.get("exercise_id"), user_id=current_user.id).first()
        if not exercise:
            continue  # ignore anything that doesn't belong to this user
        work_seconds = _to_int(entry.get("work_seconds"))
        # A timed/cardio exercise's measured work time IS its duration --
        # no need to make the user re-type a time they just watched tick by.
        actual_duration = work_seconds if exercise.target_duration_seconds is not None else None
        db.session.add(WorkoutLog(
            session_id=workout_session.id,
            exercise_id=exercise.id,
            actual_sets=_to_int(entry.get("sets")),
            actual_reps=_to_int(entry.get("reps")),
            actual_weight_kg=display_to_kg(entry.get("weight"), unit_settings.weight_unit),
            actual_distance_km=display_to_km(entry.get("distance"), unit_settings.distance_unit),
            actual_duration_seconds=actual_duration,
            started_at=entry.get("started_at"),
            work_seconds=work_seconds,
            rest_seconds=_to_int(entry.get("rest_seconds")),
        ))

    db.session.commit()
    return jsonify({"redirect": url_for("guided.story", session_id=workout_session.id)})


@guided_bp.route("/story/<int:session_id>")
@login_required
def story(session_id):
    """
    Renders a session as an animated storyline. Originally built for
    Guided Session mode but works for ANY WorkoutSession -- History now
    links every logged session here (see workouts/history.html) --
    since it degrades gracefully when work/rest timing wasn't captured
    (i.e. sessions logged the old-fashioned manual way).
    """
    workout_session = WorkoutSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    logs = sorted(
        workout_session.logs,
        key=lambda log: (log.started_at or "", log.id),
    )
    total_work = sum(log.work_seconds or 0 for log in logs)
    total_rest = sum(log.rest_seconds or 0 for log in logs)
    has_timing_data = any(log.work_seconds is not None or log.rest_seconds is not None for log in logs)

    return render_template(
        "guided/story.html",
        session=workout_session,
        logs=logs,
        settings=current_user.settings,
        total_work=total_work,
        total_rest=total_rest,
        has_timing_data=has_timing_data,
    )


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
