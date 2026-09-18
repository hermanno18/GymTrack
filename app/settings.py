from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def edit():
    user_settings = current_user.settings

    if request.method == "POST":
        weight_unit = request.form.get("weight_unit")
        distance_unit = request.form.get("distance_unit")

        if weight_unit in ("kg", "lb"):
            user_settings.weight_unit = weight_unit
        if distance_unit in ("km", "mi"):
            user_settings.distance_unit = distance_unit

        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("settings.edit"))

    return render_template("settings.html", settings=user_settings)
