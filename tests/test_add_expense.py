"""Tests for the Add Expense feature (Step 7)."""
from database.db import get_db
from database.queries import insert_expense


VALID_FORM = {
    "amount": "50.00",
    "category": "Food",
    "date": "2026-03-20",
    "description": "Lunch",
}


def _select_one(sql, params):
    conn = get_db()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# insert_expense unit tests                                           #
# ------------------------------------------------------------------ #

def test_insert_expense_inserts_row(app, test_user_id):
    new_id = insert_expense(test_user_id, 50.0, "Food", "2026-03-20", "Lunch")

    row = _select_one(
        "SELECT user_id, amount, category, date, description FROM expenses WHERE id = ?",
        (new_id,),
    )
    assert row is not None
    assert row["user_id"] == test_user_id
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


def test_insert_expense_with_none_description(app, test_user_id):
    new_id = insert_expense(test_user_id, 12.5, "Other", "2026-03-21", None)

    row = _select_one(
        "SELECT description FROM expenses WHERE id = ?",
        (new_id,),
    )
    assert row is not None
    assert row["description"] is None


# ------------------------------------------------------------------ #
# GET /expenses/add                                                   #
# ------------------------------------------------------------------ #

def test_get_add_expense_unauthenticated_redirects(client):
    response = client.get("/expenses/add", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_get_add_expense_authenticated_renders(auth_client):
    response = auth_client.get("/expenses/add")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "<form" in body
    assert 'method="POST"' in body
    for category in ("Food", "Transport", "Bills", "Health",
                     "Entertainment", "Shopping", "Other"):
        assert category in body


# ------------------------------------------------------------------ #
# POST /expenses/add                                                  #
# ------------------------------------------------------------------ #

def test_post_add_expense_unauthenticated_redirects(client):
    response = client.post("/expenses/add", data=VALID_FORM, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    row = _select_one("SELECT COUNT(*) AS n FROM expenses", ())
    assert row["n"] == 0


def test_post_add_expense_valid_redirects_and_inserts(auth_client, app):
    response = auth_client.post("/expenses/add", data=VALID_FORM, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses "
        "WHERE category = ? AND date = ?",
        ("Food", "2026-03-20"),
    )
    assert row is not None
    assert row["amount"] == 50.0
    assert row["description"] == "Lunch"


def test_post_add_expense_missing_amount_rerenders(auth_client):
    data = {**VALID_FORM, "amount": ""}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Amount is required" in body


def test_post_add_expense_zero_amount_rerenders(auth_client):
    data = {**VALID_FORM, "amount": "0"}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "greater than zero" in body


def test_post_add_expense_non_numeric_amount_rerenders(auth_client):
    data = {**VALID_FORM, "amount": "abc"}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Amount must be a number" in body


def test_post_add_expense_invalid_category_rerenders(auth_client):
    data = {**VALID_FORM, "category": "Crypto"}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "valid category" in body


def test_post_add_expense_invalid_date_rerenders(auth_client):
    data = {**VALID_FORM, "date": "not-a-date"}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "valid date" in body


def test_post_add_expense_no_description_inserts_null(auth_client, app):
    data = {**VALID_FORM, "description": ""}
    response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    row = _select_one(
        "SELECT description FROM expenses WHERE category = ? AND date = ?",
        ("Food", "2026-03-20"),
    )
    assert row is not None
    assert row["description"] is None
