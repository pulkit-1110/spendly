from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    """Return dict with name, email, member_since (formatted "Month YYYY") or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    try:
        member_since = datetime.strptime(
            row["created_at"], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B %Y")
    except (TypeError, ValueError):
        member_since = row["created_at"]

    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": member_since,
    }


def _build_date_where(user_id, start_date, end_date):
    """Build a parameterised WHERE clause for user + optional ISO date range."""
    clauses = ["user_id = ?"]
    params = [user_id]
    if start_date:
        clauses.append("date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("date <= ?")
        params.append(end_date)
    return " AND ".join(clauses), params


def get_summary_stats(user_id, start_date=None, end_date=None):
    """Return total_spent, transaction_count, top_category for a user."""
    where, params = _build_date_where(user_id, start_date, end_date)
    conn = get_db()
    try:
        totals = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(amount), 0.0) AS total "
            "FROM expenses WHERE " + where,
            params,
        ).fetchone()

        top = conn.execute(
            "SELECT category, SUM(amount) AS s "
            "FROM expenses WHERE " + where + " "
            "GROUP BY category "
            "ORDER BY s DESC, category ASC "
            "LIMIT 1",
            params,
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent": float(totals["total"]),
        "transaction_count": int(totals["n"]),
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, start_date=None, end_date=None, limit=10):
    """Return list of recent transactions for a user, newest first."""
    where, params = _build_date_where(user_id, start_date, end_date)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount "
            "FROM expenses WHERE " + where + " "
            "ORDER BY date DESC, id DESC "
            "LIMIT ?",
            params + [limit],
        ).fetchall()
    finally:
        conn.close()

    transactions = []
    for row in rows:
        try:
            display_date = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y")
        except (TypeError, ValueError):
            display_date = row["date"]
        transactions.append({
            "date": display_date,
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        })
    return transactions


def get_category_breakdown(user_id, start_date=None, end_date=None):
    """Return list of {name, amount, pct} dicts ordered by amount desc.

    Percentages are integers that sum to exactly 100. The largest
    category absorbs any rounding remainder. Returns [] when there
    are no expenses for this user.
    """
    where, params = _build_date_where(user_id, start_date, end_date)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category AS name, SUM(amount) AS amount "
            "FROM expenses WHERE " + where + " "
            "GROUP BY category "
            "ORDER BY amount DESC",
            params,
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    total = sum(row["amount"] for row in rows)
    if total == 0:
        return []

    items = [
        {
            "name": row["name"],
            "amount": float(row["amount"]),
            "pct": int(round(row["amount"] / total * 100)),
        }
        for row in rows
    ]

    # Adjust the largest (first) item so percentages sum to exactly 100.
    diff = 100 - sum(item["pct"] for item in items)
    if items:
        items[0]["pct"] += diff

    return items


def insert_expense(user_id, amount, category, date, description):
    """Insert a new expense row. Returns the new expense id."""
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
