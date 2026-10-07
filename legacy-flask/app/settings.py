from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db
from .models import User

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def edit():
    user_settings = current_user.settings

    if request.method == "POST":
        # The page hosts three independent <form>s (units / email /
        # password), each posting here with a hidden "form_name" field --
        # keeps this as one simple GET+POST resource instead of three URLs.
        form_name = request.form.get("form_name")
        if form_name == "units":
            _update_units(user_settings)
        elif form_name == "email":
            _update_email()
        elif form_name == "password":
            _update_password()
        return redirect(url_for("settings.edit"))

    return render_template("settings.html", settings=user_settings)


def _update_units(user_settings):
    weight_unit = request.form.get("weight_unit")
    distance_unit = request.form.get("distance_unit")

    if weight_unit in ("kg", "lb"):
        user_settings.weight_unit = weight_unit
    if distance_unit in ("km", "mi"):
        user_settings.distance_unit = distance_unit

    db.session.commit()
    flash("Settings saved.", "success")


def _update_email():
    current_password = request.form.get("current_password", "")
    new_email = request.form.get("new_email", "").strip().lower()

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return
    if not new_email or "@" not in new_email:
        flash("Enter a valid email address.", "error")
        return
    if new_email == current_user.email:
        flash("That's already your email.", "error")
        return
    if User.query.filter_by(email=new_email).first():
        flash("That email is already in use.", "error")
        return

    current_user.email = new_email
    db.session.commit()
    flash("Email updated.", "success")


def _update_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
        return
    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "error")
        return
    if new_password != confirm_password:
        flash("New passwords don't match.", "error")
        return

    current_user.set_password(new_password)
    db.session.commit()
    flash("Password updated.", "success")
