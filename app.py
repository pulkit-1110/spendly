import re
from flask import Flask, render_template, request, flash, redirect, url_for, session

from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'


def validate_registration_form(name, email, password, password_confirm):
    """Validate registration form data. Returns list of errors."""
    errors = []

    # Name validation
    if not name or not name.strip():
        errors.append("Full name is required")
    elif len(name.strip()) < 2:
        errors.append("Full name must be at least 2 characters")

    # Email validation
    if not email:
        errors.append("Email address is required")
    elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append("Please enter a valid email address")

    # Password validation
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters")

    # Password confirmation
    if not password_confirm:
        errors.append("Please confirm your password")
    elif password != password_confirm:
        errors.append("Passwords do not match")

    return errors

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        # Validate form data
        errors = validate_registration_form(name, email, password, password_confirm)

        if errors:
            for error in errors:
                flash(error)
            return render_template("register.html")

        # Attempt to create user
        user_id = create_user(name, email, password)

        if user_id is None:
            flash("An account with this email address already exists")
            return render_template("register.html")

        # Success - redirect to login with success message
        flash("Account created successfully! Please sign in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("landing"))
        return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
