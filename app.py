import re
from datetime import date, datetime

from flask import Flask, render_template, request, flash, redirect, url_for, session

from werkzeug.security import check_password_hash

from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
)
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    insert_expense,
)


EXPENSE_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'


# View helpers


def _parse_iso_date(value):
    """Return a date for an ISO YYYY-MM-DD string, or None if invalid/missing."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _format_filter_label(start, end):
    """Build the 'Showing …' label or return None when no filter is active."""
    if start and end:
        return f"Showing {start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')}"
    if start:
        return f"Showing from {start.strftime('%d %b %Y')}"
    if end:
        return f"Showing up to {end.strftime('%d %b %Y')}"
    return None


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


def validate_expense_form(amount, category, date_str, description):
    """Validate add-expense form data.

    Returns (errors, cleaned). `cleaned` is meaningful only when errors == [].
    Long descriptions are silently truncated to 200 characters.
    """
    errors = []
    cleaned = {}

    # Amount
    if not amount:
        errors.append("Amount is required")
    else:
        try:
            amount_value = float(amount)
        except ValueError:
            errors.append("Amount must be a number")
        else:
            if amount_value <= 0:
                errors.append("Amount must be greater than zero")
            else:
                cleaned["amount"] = amount_value

    # Category
    if not category:
        errors.append("Category is required")
    elif category not in EXPENSE_CATEGORIES:
        errors.append("Please choose a valid category")
    else:
        cleaned["category"] = category

    # Date
    if not date_str:
        errors.append("Date is required")
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("Please enter a valid date (YYYY-MM-DD)")
        else:
            cleaned["date"] = date_str

    # Description (optional, silent truncate at 200)
    trimmed = (description or "").strip()
    cleaned["description"] = trimmed[:200] if trimmed else None

    return errors, cleaned


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
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if user is None:
        session.clear()
        flash("Please log in to view your profile.")
        return redirect(url_for("login"))

    start = _parse_iso_date(request.args.get("start_date"))
    end = _parse_iso_date(request.args.get("end_date"))
    if start and end and start > end:
        start, end = end, start

    start_iso = start.isoformat() if start else None
    end_iso = end.isoformat() if end else None

    summary = get_summary_stats(user_id, start_date=start_iso, end_date=end_iso)
    transactions = get_recent_transactions(user_id, start_date=start_iso, end_date=end_iso)
    categories = get_category_breakdown(user_id, start_date=start_iso, end_date=end_iso)

    return render_template(
        "profile.html",
        user=user,
        summary=summary,
        transactions=transactions,
        categories=categories,
        start_date=start_iso,
        end_date=end_iso,
        filter_label=_format_filter_label(start, end),
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        flash("Please log in to view analytics.")
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to add an expense.")
        return redirect(url_for("login"))

    if request.method == "POST":
        errors, cleaned = validate_expense_form(
            request.form.get("amount", "").strip(),
            request.form.get("category", "").strip(),
            request.form.get("date", "").strip(),
            request.form.get("description", ""),
        )
        if errors:
            for error in errors:
                flash(error)
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                today=date.today().isoformat(),
            )

        insert_expense(
            user_id,
            cleaned["amount"],
            cleaned["category"],
            cleaned["date"],
            cleaned["description"],
        )
        return redirect(url_for("profile"))

    return render_template(
        "add_expense.html",
        categories=EXPENSE_CATEGORIES,
        today=date.today().isoformat(),
    )


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
