"""Tests for the Edit Expense feature (Step 8)."""
from database.db import get_db, create_user
from database.queries import insert_expense, get_expense_by_id, update_expense


VALID_FORM = {
    "amount": "75.50",
    "category": "Transport",
    "date": "2026-04-01",
    "description": "Updated cab ride",
}


def _select_one(sql, params):
    conn = get_db()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def _seed_expense(user_id):
    return insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")


# ------------------------------------------------------------------ #
# get_expense_by_id / update_expense unit tests                       #
# ------------------------------------------------------------------ #

def test_get_expense_by_id_returns_row(app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    row = get_expense_by_id(expense_id)
    assert row is not None
    assert row["id"] == expense_id
    assert row["user_id"] == test_user_id
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


def test_get_expense_by_id_returns_none_when_missing(app):
    assert get_expense_by_id(99999) is None


def test_update_expense_updates_row(app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    rows_updated = update_expense(
        expense_id, test_user_id, 75.5, "Transport", "2026-04-01", "Updated cab ride",
    )
    assert rows_updated == 1

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    )
    assert row["amount"] == 75.5
    assert row["category"] == "Transport"
    assert row["date"] == "2026-04-01"
    assert row["description"] == "Updated cab ride"


def test_update_expense_does_not_update_other_users_row(app, test_user_id):
    expense_id = _seed_expense(test_user_id)
    other_user_id = create_user("Other User", "other@example.com", "otherpass123")

    rows_updated = update_expense(
        expense_id, other_user_id, 999.0, "Bills", "2026-05-01", "Hijack",
    )
    assert rows_updated == 0

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    )
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


# ------------------------------------------------------------------ #
# GET /expenses/<id>/edit                                             #
# ------------------------------------------------------------------ #

def test_get_edit_expense_unauthenticated_redirects(client, app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    response = client.get(f"/expenses/{expense_id}/edit", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_get_edit_expense_authenticated_renders_with_prefill(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 42.25, "Bills", "2026-02-15", "Electric")

    response = auth_client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<form" in body
    assert 'method="POST"' in body
    assert "42.25" in body
    assert "2026-02-15" in body
    assert "Electric" in body
    for category in ("Food", "Transport", "Bills", "Health",
                     "Entertainment", "Shopping", "Other"):
        assert category in body


def test_get_edit_expense_missing_returns_404(auth_client):
    response = auth_client.get("/expenses/99999/edit")
    assert response.status_code == 404


def test_get_edit_expense_other_user_returns_404(auth_client):
    other_user_id = create_user("Other User", "other@example.com", "otherpass123")
    expense_id = insert_expense(other_user_id, 30.0, "Health", "2026-03-10", "Pharmacy")

    response = auth_client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 404


# ------------------------------------------------------------------ #
# POST /expenses/<id>/edit                                            #
# ------------------------------------------------------------------ #

def test_post_edit_expense_unauthenticated_redirects(client, app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    response = client.post(
        f"/expenses/{expense_id}/edit", data=VALID_FORM, follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    row = _select_one(
        "SELECT amount, category FROM expenses WHERE id = ?", (expense_id,),
    )
    assert row["amount"] == 50.0
    assert row["category"] == "Food"


def test_post_edit_expense_valid_redirects_and_updates(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=VALID_FORM, follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    )
    assert row["amount"] == 75.5
    assert row["category"] == "Transport"
    assert row["date"] == "2026-04-01"
    assert row["description"] == "Updated cab ride"


def test_post_edit_expense_other_user_returns_404_and_does_not_update(auth_client):
    other_user_id = create_user("Other User", "other@example.com", "otherpass123")
    expense_id = insert_expense(other_user_id, 30.0, "Health", "2026-03-10", "Pharmacy")

    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=VALID_FORM, follow_redirects=False,
    )
    assert response.status_code == 404

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    )
    assert row["amount"] == 30.0
    assert row["category"] == "Health"
    assert row["date"] == "2026-03-10"
    assert row["description"] == "Pharmacy"


def test_post_edit_expense_missing_amount_rerenders(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    data = {**VALID_FORM, "amount": ""}
    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=data, follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Amount is required" in response.get_data(as_text=True)

    row = _select_one("SELECT amount FROM expenses WHERE id = ?", (expense_id,))
    assert row["amount"] == 50.0


def test_post_edit_expense_invalid_category_rerenders(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    data = {**VALID_FORM, "category": "Crypto"}
    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=data, follow_redirects=True,
    )
    assert response.status_code == 200
    assert "valid category" in response.get_data(as_text=True)

    row = _select_one("SELECT category FROM expenses WHERE id = ?", (expense_id,))
    assert row["category"] == "Food"


def test_post_edit_expense_invalid_date_rerenders(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    data = {**VALID_FORM, "date": "not-a-date"}
    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=data, follow_redirects=True,
    )
    assert response.status_code == 200
    assert "valid date" in response.get_data(as_text=True)

    row = _select_one("SELECT date FROM expenses WHERE id = ?", (expense_id,))
    assert row["date"] == "2026-03-20"


def test_post_edit_expense_empty_description_saves_null(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    data = {**VALID_FORM, "description": ""}
    response = auth_client.post(
        f"/expenses/{expense_id}/edit", data=data, follow_redirects=False,
    )
    assert response.status_code == 302

    row = _select_one("SELECT description FROM expenses WHERE id = ?", (expense_id,))
    assert row["description"] is None
