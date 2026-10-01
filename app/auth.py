from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import hashlib

from . import db
from .models import User, UserSettings
from .mailer import send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

RESET_TOKEN_MAX_AGE_SECONDS = 30 * 60


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


@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = _make_reset_token(user)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(user.email, reset_url)
        # Identical message whether or not the email is registered --
        # never let this form be used to probe which emails have accounts.
        flash("If that email has an account, a reset link is on its way.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot.html")


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    user = _verify_reset_token(token)
    if not user:
        flash("That reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(new_password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif new_password != confirm:
            flash("Passwords don't match.", "error")
        else:
            user.set_password(new_password)
            db.session.commit()
            flash("Password reset. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset.html", token=token)


def _reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="password-reset")


def _password_fingerprint(user):
    # werkzeug's hash format is 'method$salt$digest' where the 'method'
    # segment (e.g. 'scrypt:32768:8:1$') is a FIXED-length constant for
    # a given werkzeug version/config -- slicing the raw hash itself
    # would therefore produce an IDENTICAL fingerprint for every user's
    # every password. Hashing the whole string first ties the
    # fingerprint to the actual salt+digest, so it's guaranteed to
    # change whenever the password does.
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def _make_reset_token(user):
    # Embedding a fingerprint of the CURRENT password hash makes the
    # token self-invalidating the moment it's used (or the password
    # changes some other way) -- no database table of issued/used
    # tokens needed.
    return _reset_serializer().dumps({"user_id": user.id, "pw_fingerprint": _password_fingerprint(user)})


def _verify_reset_token(token):
    """Returns the User if the token is well-formed, unexpired, and the
    password hasn't changed since it was issued. None otherwise."""
    try:
        data = _reset_serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    user = db.session.get(User, data.get("user_id"))
    if not user or _password_fingerprint(user) != data.get("pw_fingerprint"):
        return None
    return user
