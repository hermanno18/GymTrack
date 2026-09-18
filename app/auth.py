from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import db
from .models import User, UserSettings

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = _validate_registration(email, password, confirm)
        if error:
            flash(error, "error")
        else:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            db.session.add(UserSettings(user_id=user.id))
            db.session.commit()
            login_user(user)
            return redirect(url_for("dashboard.home"))

    return render_template("auth/register.html")


def _validate_registration(email, password, confirm):
    if not email or not password:
        return "Email and password are required."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if password != confirm:
        return "Passwords don't match."
    if User.query.filter_by(email=email).first():
        return "An account with that email already exists."
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard.home"))
        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
