from flask import Blueprint, render_template
from flask_login import login_required, current_user

from .models import Program, WorkoutSession

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


@dashboard_bp.route("/")
@login_required
def home():
    programs = (
        Program.query.filter_by(user_id=current_user.id)
        .order_by(Program.created_at.desc())
        .all()
    )
    recent_sessions = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutSession.date.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "dashboard.html", programs=programs, recent_sessions=recent_sessions
    )
