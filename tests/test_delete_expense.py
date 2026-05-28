"""Tests for the Delete Expense feature (Step 9)."""
from database.db import get_db, create_user
from database.queries import insert_expense, delete_expense


def _select_one(sql, params):
    conn = get_db()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def _seed_expense(user_id):
    return insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")


# ------------------------------------------------------------------ #
# delete_expense unit tests                                           #
# ------------------------------------------------------------------ #

def test_delete_expense_removes_row(app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    rows_deleted = delete_expense(expense_id, test_user_id)
    assert rows_deleted == 1

    row = _select_one("SELECT id FROM expenses WHERE id = ?", (expense_id,))
    assert row is None


def test_delete_expense_wrong_user_does_not_delete(app, test_user_id):
    expense_id = _seed_expense(test_user_id)
    other_user_id = create_user("Other User", "other@example.com", "otherpass123")

    rows_deleted = delete_expense(expense_id, other_user_id)
    assert rows_deleted == 0

    row = _select_one(
        "SELECT amount, category, date, description FROM expenses WHERE id = ?",
        (expense_id,),
    )
    assert row is not None
    assert row["amount"] == 50.0
    assert row["category"] == "Food"


def test_delete_expense_nonexistent_id_no_error(app):
    rows_deleted = delete_expense(99999, 1)
    assert rows_deleted == 0


# ------------------------------------------------------------------ #
# POST /expenses/<id>/delete                                          #
# ------------------------------------------------------------------ #

def test_post_delete_unauthenticated_redirects(client, app, test_user_id):
    expense_id = _seed_expense(test_user_id)

    response = client.post(f"/expenses/{expense_id}/delete", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    row = _select_one("SELECT id FROM expenses WHERE id = ?", (expense_id,))
    assert row is not None


def test_post_delete_own_expense_redirects_and_removes(auth_client):
    user_row = _select_one("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    expense_id = insert_expense(user_row["id"], 50.0, "Food", "2026-03-20", "Lunch")

    response = auth_client.post(
        f"/expenses/{expense_id}/delete", follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    row = _select_one("SELECT id FROM expenses WHERE id = ?", (expense_id,))
    assert row is None


def test_post_delete_other_user_expense_returns_404_and_keeps_row(auth_client):
    other_user_id = create_user("Other User", "other@example.com", "otherpass123")
    expense_id = insert_expense(other_user_id, 30.0, "Health", "2026-03-10", "Pharmacy")

    response = auth_client.post(
        f"/expenses/{expense_id}/delete", follow_redirects=False,
    )
    assert response.status_code == 404

    row = _select_one(
        "SELECT amount, category FROM expenses WHERE id = ?", (expense_id,),
    )
    assert row is not None
    assert row["amount"] == 30.0
    assert row["category"] == "Health"


def test_post_delete_nonexistent_id_returns_404(auth_client):
    response = auth_client.post("/expenses/99999/delete", follow_redirects=False)
    assert response.status_code == 404


def test_get_delete_returns_405(auth_client):
    response = auth_client.get("/expenses/1/delete", follow_redirects=False)
    assert response.status_code == 405
