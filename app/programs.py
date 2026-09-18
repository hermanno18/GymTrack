"""
Program-level routes: list, create (upload PDF or start from scratch),
delete. Day/exercise editing lives in builder.py -- kept separate so
neither file grows unwieldy.
"""
import os
import uuid

import pdfplumber
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import Program, ProgramDay, Exercise
from .pdf_parser import parse_program_text
from .utils import normalize_name

programs_bp = Blueprint("programs", __name__, url_prefix="/programs")


@programs_bp.route("/")
@login_required
def list_programs():
    programs = (
        Program.query.filter_by(user_id=current_user.id)
        .order_by(Program.created_at.desc())
        .all()
    )
    return render_template("programs/list.html", programs=programs)


@programs_bp.route("/new")
@login_required
def new():
    return render_template("programs/new.html")


@programs_bp.route("/new/manual", methods=["POST"])
@login_required
def new_manual():
    name = request.form.get("name", "").strip() or "My Program"
    program = Program(user_id=current_user.id, name=name)
    db.session.add(program)
    db.session.commit()
    flash("Program created. Add your days and exercises below.", "success")
    return redirect(url_for("builder.edit_program", program_id=program.id))


@programs_bp.route("/new/upload", methods=["POST"])
@login_required
def new_upload():
    uploaded = request.files.get("pdf")
    if not uploaded or uploaded.filename == "":
        flash("Please choose a PDF file to upload.", "error")
        return redirect(url_for("programs.new"))

    if not uploaded.filename.lower().endswith(".pdf"):
        flash("Only PDF files are supported.", "error")
        return redirect(url_for("programs.new"))

    raw_text, save_error = _extract_pdf_text(uploaded)
    if save_error:
        flash(save_error, "error")
        return redirect(url_for("programs.new"))

    name = request.form.get("name", "").strip() or uploaded.filename.rsplit(".", 1)[0]
    program = Program(
        user_id=current_user.id,
        name=name,
        source_pdf_filename=secure_filename(uploaded.filename),
        raw_text=raw_text,
    )
    db.session.add(program)
    db.session.flush()

    parsed_days = parse_program_text(raw_text) if raw_text else []
    if not parsed_days:
        db.session.commit()
        flash(
            "Couldn't automatically read exercises from that PDF. "
            "No worries -- add your days and exercises manually below.",
            "warning",
        )
        return redirect(url_for("builder.edit_program", program_id=program.id))

    _create_days_and_exercises(program, parsed_days)
    db.session.commit()
    flash(
        "Program imported! Please review the extracted exercises below "
        "before you start logging workouts.",
        "success",
    )
    return redirect(url_for("builder.edit_program", program_id=program.id))


def _extract_pdf_text(uploaded_file):
    """Save the upload to a temp path, extract text, clean up. Returns (text, error)."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    temp_name = f"{uuid.uuid4().hex}.pdf"
    temp_path = os.path.join(upload_folder, temp_name)
    uploaded_file.save(temp_path)

    try:
        with pdfplumber.open(temp_path) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages_text), None
    except Exception:
        return None, (
            "That file couldn't be read as a PDF (it may be scanned/image-only "
            "or corrupted). You can still build your program manually below."
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _create_days_and_exercises(program, parsed_days):
    for day_index, day in enumerate(parsed_days):
        program_day = ProgramDay(
            program_id=program.id, label=day["label"], order_index=day_index
        )
        db.session.add(program_day)
        db.session.flush()

        for exercise_data in day["exercises"]:
            db.session.add(Exercise(
                program_day_id=program_day.id,
                user_id=program.user_id,
                name=exercise_data["name"],
                name_normalized=normalize_name(exercise_data["name"]),
                target_sets=exercise_data.get("sets"),
                target_reps=exercise_data.get("reps"),
                target_weight_kg=exercise_data.get("weight_kg"),
                target_distance_km=exercise_data.get("distance_km"),
                order_index=exercise_data.get("order_index", 0),
            ))


@programs_bp.route("/<int:program_id>/delete", methods=["POST"])
@login_required
def delete(program_id):
    program = Program.query.filter_by(id=program_id, user_id=current_user.id).first_or_404()
    db.session.delete(program)
    db.session.commit()
    flash("Program deleted.", "success")
    return redirect(url_for("programs.list_programs"))
