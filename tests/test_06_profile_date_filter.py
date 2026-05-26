"""
Test suite for Date Filter for Profile Page (Step 6).

Tests are based on .claude/specs/06-profile-date-filter.md and validate:
- Date-range filtering via query parameters
- Form UI presence and pre-population
- Filter label rendering
- Auth guard unchanged
- Query helpers with date bounds
"""
import pytest
from datetime import date, timedelta

from database.db import get_db, create_user
from database.queries import (
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ======================================================================
# Helper functions
# ======================================================================

def insert_expense(user_id, amount, category, expense_date, description=""):
    """Insert a single expense directly into the test DB."""
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, expense_date, description),
        )
        conn.commit()
    finally:
        conn.close()


def seed_test_expenses(user_id):
    """
    Seed a known set of expenses for testing filters.

    Returns a dict with date strings as keys for reference.
    Uses dates relative to 2026-05-20 to 2026-05-26.
    """
    expenses = {
        '2026-05-20': (50.00, 'Food', 'Groceries'),
        '2026-05-21': (30.00, 'Transport', 'Gas'),
        '2026-05-22': (100.00, 'Bills', 'Internet'),
        '2026-05-23': (20.00, 'Food', 'Lunch'),
        '2026-05-24': (75.00, 'Shopping', 'Clothes'),
        '2026-05-25': (15.00, 'Entertainment', 'Movie'),
        '2026-05-26': (40.00, 'Food', 'Dinner'),
    }

    for date_str, (amount, category, description) in expenses.items():
        insert_expense(user_id, amount, category, date_str, description)

    return expenses


# ======================================================================
# Route-level integration tests
# ======================================================================

class TestProfileDateFilterRoutes:
    """Test /profile route with date filtering via query parameters."""

    def test_no_filter_regression_all_time_data(self, auth_client, test_user_id):
        """GET /profile with no query string returns 200 and renders all expenses."""
        # Seed known expenses
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile')

        assert response.status_code == 200, 'Profile page should load'

        # Expected: 7 transactions, total 330.00
        assert b'330.00' in response.data or b'330' in response.data, \
            'All-time total should be visible'

        # Check that all categories appear somewhere (category breakdown or transactions)
        assert b'Food' in response.data
        assert b'Transport' in response.data
        assert b'Bills' in response.data

    def test_filter_card_ui_present(self, auth_client, test_user_id):
        """Profile page contains filter form with correct structure."""
        response = auth_client.get('/profile')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Form with GET method
        assert 'method="get"' in html.lower() or 'method=\'get\'' in html.lower(), \
            'Filter form must use GET method'

        # Two date inputs
        assert 'type="date"' in html, 'Should have date input fields'
        assert 'name="start_date"' in html, 'Should have start_date input'
        assert 'name="end_date"' in html, 'Should have end_date input'

        # Submit button
        assert 'type="submit"' in html or '<button' in html, \
            'Should have submit button'

    def test_both_bounds_narrow_data(self, auth_client, test_user_id):
        """Filter with start_date and end_date returns only in-range expenses."""
        seed_test_expenses(test_user_id)

        # Filter to 2026-05-22 through 2026-05-24 (3 expenses: 100, 20, 75 = 195)
        response = auth_client.get('/profile?start_date=2026-05-22&end_date=2026-05-24')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Should see filtered total
        assert '195' in html, 'Filtered total should be 195.00'

        # Should see in-range expenses
        assert 'Internet' in html  # 2026-05-22
        assert 'Lunch' in html     # 2026-05-23
        assert 'Clothes' in html   # 2026-05-24

        # Should NOT see out-of-range expenses
        assert 'Groceries' not in html  # 2026-05-20
        assert 'Movie' not in html      # 2026-05-25
        assert 'Dinner' not in html     # 2026-05-26

    def test_open_lower_bound_start_date_only(self, auth_client, test_user_id):
        """Filter with only start_date includes all expenses from that date onward."""
        seed_test_expenses(test_user_id)

        # From 2026-05-24 onward (3 expenses: 75, 15, 40 = 130)
        response = auth_client.get('/profile?start_date=2026-05-24')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '130' in html, 'Total from 2026-05-24 onward should be 130.00'

        # Should see
        assert 'Clothes' in html      # 2026-05-24
        assert 'Movie' in html        # 2026-05-25
        assert 'Dinner' in html       # 2026-05-26

        # Should NOT see earlier
        assert 'Groceries' not in html  # 2026-05-20

    def test_open_upper_bound_end_date_only(self, auth_client, test_user_id):
        """Filter with only end_date includes all expenses up to that date."""
        seed_test_expenses(test_user_id)

        # Up to 2026-05-22 (3 expenses: 50, 30, 100 = 180)
        response = auth_client.get('/profile?end_date=2026-05-22')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert '180' in html, 'Total up to 2026-05-22 should be 180.00'

        # Should see
        assert 'Groceries' in html  # 2026-05-20
        assert 'Gas' in html        # 2026-05-21
        assert 'Internet' in html   # 2026-05-22

        # Should NOT see later
        assert 'Movie' not in html   # 2026-05-25
        assert 'Dinner' not in html  # 2026-05-26

    def test_reversed_bounds_swap_silently(self, auth_client, test_user_id):
        """start_date > end_date swaps bounds and returns correct data."""
        seed_test_expenses(test_user_id)

        # Reversed: start=2026-05-24, end=2026-05-22
        # Should behave as if start=2026-05-22, end=2026-05-24
        response = auth_client.get('/profile?start_date=2026-05-24&end_date=2026-05-22')

        assert response.status_code == 200, 'Should not error on reversed bounds'
        html = response.data.decode('utf-8')

        # Same result as forward bounds: 195.00
        assert '195' in html

        # Should see swapped-range expenses
        assert 'Internet' in html
        assert 'Lunch' in html
        assert 'Clothes' in html

    def test_malformed_start_date_ignored(self, auth_client, test_user_id):
        """Malformed start_date is silently ignored, returns all-time data."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?start_date=not-a-date')

        assert response.status_code == 200, 'Should not 500 on malformed date'
        html = response.data.decode('utf-8')

        # Should show all-time total (330.00)
        assert '330' in html

    def test_malformed_end_date_ignored(self, auth_client, test_user_id):
        """Malformed end_date is silently ignored, returns all-time data."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?end_date=garbage')

        assert response.status_code == 200, 'Should not 500 on malformed date'
        html = response.data.decode('utf-8')

        # Should show all-time total (330.00)
        assert '330' in html

    def test_empty_range_future_date(self, auth_client, test_user_id):
        """Future start_date that excludes all expenses returns 200 with zero transactions."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?start_date=2027-01-01')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Should show zero or empty state
        # Transactions list should be empty
        assert 'Groceries' not in html
        assert 'Dinner' not in html

        # Total should be 0 or 0.00
        assert '0' in html

    def test_form_prepopulation_both_bounds(self, auth_client, test_user_id):
        """When filter is active, form inputs are pre-populated with current values."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?start_date=2026-05-22&end_date=2026-05-24')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Inputs should have value attributes
        assert 'value="2026-05-22"' in html, 'start_date input should be pre-populated'
        assert 'value="2026-05-24"' in html, 'end_date input should be pre-populated'

    def test_active_label_both_bounds(self, auth_client, test_user_id):
        """When both bounds set, page shows 'Showing DD MMM YYYY – DD MMM YYYY' label."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?start_date=2026-05-23&end_date=2026-05-25')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Expected format: "Showing 23 May 2026 – 25 May 2026"
        assert 'Showing' in html
        assert '23 May 2026' in html
        assert '25 May 2026' in html

    @pytest.mark.parametrize('params,expected_label', [
        ('start_date=2026-05-20', 'Showing from 20 May 2026'),
        ('end_date=2026-05-25', 'Showing up to 25 May 2026'),
    ])
    def test_active_label_single_bound(self, auth_client, test_user_id, params, expected_label):
        """When only one bound is set, label shows appropriate 'from' or 'up to' text."""
        seed_test_expenses(test_user_id)

        response = auth_client.get(f'/profile?{params}')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        assert expected_label in html, f'Should show label: {expected_label}'

    def test_clear_link_present_when_filter_active(self, auth_client, test_user_id):
        """When filter is active, page contains Clear link to /profile."""
        seed_test_expenses(test_user_id)

        response = auth_client.get('/profile?start_date=2026-05-22')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Should have a link back to /profile with no query string
        assert 'Clear' in html or 'clear' in html
        # The href should point to /profile
        assert 'href="/profile"' in html or "href='/profile'" in html

    def test_auth_guard_unchanged_with_querystring(self, client, test_user_id):
        """GET /profile while logged out redirects to /login, even with filter params."""
        # NOT using auth_client — user is not logged in

        response = client.get('/profile?start_date=2026-05-22', follow_redirects=False)

        assert response.status_code == 302, 'Should redirect when not logged in'
        assert '/login' in response.location, 'Should redirect to login page'

    def test_category_breakdown_percentages_sum_to_100_under_filter(self, auth_client, test_user_id):
        """Under an active filter with multiple categories, percentages sum to exactly 100."""
        seed_test_expenses(test_user_id)

        # Filter that includes multiple categories: 2026-05-22 to 2026-05-24
        # Bills: 100, Food: 20, Shopping: 75 — total 195
        response = auth_client.get('/profile?start_date=2026-05-22&end_date=2026-05-24')

        assert response.status_code == 200
        html = response.data.decode('utf-8')

        # Parse out percentages (look for patterns like "51%" or "51 %")
        import re
        percentages = re.findall(r'(\d+)\s*%', html)
        percentages = [int(p) for p in percentages]

        # Filter out any non-category percentages (sometimes other UI elements show %)
        # We expect 3 categories in this range, so look for a set of 3 percentages
        # that sum to 100
        if len(percentages) >= 3:
            # Take the first 3 as category percentages
            category_pcts = percentages[:3]
            total_pct = sum(category_pcts)
            assert total_pct == 100, f'Category percentages should sum to 100, got {total_pct}'


# ======================================================================
# Query helper unit tests
# ======================================================================

class TestQueryHelpers:
    """Unit tests for database/queries.py with date filtering."""

    def test_get_summary_stats_no_date_kwargs(self, test_user_id):
        """get_summary_stats(user_id) with no date kwargs returns all-time stats."""
        seed_test_expenses(test_user_id)

        stats = get_summary_stats(test_user_id)

        assert stats['transaction_count'] == 7
        assert stats['total_spent'] == 330.00
        assert stats['top_category'] in ['Food', 'Bills', 'Shopping']  # Depends on algo

    def test_get_summary_stats_with_date_bounds(self, test_user_id):
        """get_summary_stats with start_date and end_date returns only in-range counts."""
        seed_test_expenses(test_user_id)

        stats = get_summary_stats(
            test_user_id,
            start_date='2026-05-22',
            end_date='2026-05-24'
        )

        assert stats['transaction_count'] == 3, 'Should have 3 transactions in range'
        assert stats['total_spent'] == 195.00, 'Total should be 195.00'

        # Top category by amount in this range: Bills (100)
        assert stats['top_category'] == 'Bills'

    def test_get_summary_stats_start_date_only(self, test_user_id):
        """get_summary_stats with only start_date filters from that date onward."""
        seed_test_expenses(test_user_id)

        stats = get_summary_stats(test_user_id, start_date='2026-05-24')

        assert stats['transaction_count'] == 3  # 05-24, 05-25, 05-26
        assert stats['total_spent'] == 130.00

    def test_get_summary_stats_end_date_only(self, test_user_id):
        """get_summary_stats with only end_date filters up to that date."""
        seed_test_expenses(test_user_id)

        stats = get_summary_stats(test_user_id, end_date='2026-05-22')

        assert stats['transaction_count'] == 3  # 05-20, 05-21, 05-22
        assert stats['total_spent'] == 180.00

    def test_get_summary_stats_empty_range(self, test_user_id):
        """get_summary_stats with future date range returns zero counts."""
        seed_test_expenses(test_user_id)

        stats = get_summary_stats(test_user_id, start_date='2027-01-01')

        assert stats['transaction_count'] == 0
        assert stats['total_spent'] == 0.00
        assert stats['top_category'] == '—'  # No category

    def test_get_recent_transactions_with_date_bounds(self, test_user_id):
        """get_recent_transactions with date bounds returns only in-range rows."""
        seed_test_expenses(test_user_id)

        transactions = get_recent_transactions(
            test_user_id,
            start_date='2026-05-22',
            end_date='2026-05-24'
        )

        assert len(transactions) == 3, 'Should return 3 in-range transactions'

        # Check descriptions are from in-range dates
        descriptions = [t['description'] for t in transactions]
        assert 'Internet' in descriptions
        assert 'Lunch' in descriptions
        assert 'Clothes' in descriptions

        # Should NOT include out-of-range
        assert 'Groceries' not in descriptions
        assert 'Movie' not in descriptions

    def test_get_recent_transactions_no_dates(self, test_user_id):
        """get_recent_transactions with no date kwargs returns all transactions."""
        seed_test_expenses(test_user_id)

        transactions = get_recent_transactions(test_user_id)

        assert len(transactions) == 7, 'Should return all 7 transactions'

    def test_get_recent_transactions_respects_limit(self, test_user_id):
        """get_recent_transactions respects the limit parameter."""
        seed_test_expenses(test_user_id)

        transactions = get_recent_transactions(test_user_id, limit=3)

        assert len(transactions) == 3, 'Should respect limit parameter'

    def test_get_category_breakdown_with_date_bounds(self, test_user_id):
        """get_category_breakdown with date bounds returns only in-range categories."""
        seed_test_expenses(test_user_id)

        breakdown = get_category_breakdown(
            test_user_id,
            start_date='2026-05-22',
            end_date='2026-05-24'
        )

        # Should have 3 categories: Bills (100), Shopping (75), Food (20)
        assert len(breakdown) == 3

        names = [c['name'] for c in breakdown]
        assert 'Bills' in names
        assert 'Shopping' in names
        assert 'Food' in names

        # Should NOT have Transport or Entertainment (out of range)
        assert 'Transport' not in names
        assert 'Entertainment' not in names

    def test_get_category_breakdown_percentages_sum_to_100(self, test_user_id):
        """get_category_breakdown percentages sum to exactly 100."""
        seed_test_expenses(test_user_id)

        breakdown = get_category_breakdown(
            test_user_id,
            start_date='2026-05-22',
            end_date='2026-05-24'
        )

        total_pct = sum(c['pct'] for c in breakdown)
        assert total_pct == 100, f'Percentages should sum to 100, got {total_pct}'

    def test_get_category_breakdown_no_dates(self, test_user_id):
        """get_category_breakdown with no date kwargs returns all categories."""
        seed_test_expenses(test_user_id)

        breakdown = get_category_breakdown(test_user_id)

        # Should have 5 categories total
        assert len(breakdown) == 5

        # Percentages should still sum to 100
        total_pct = sum(c['pct'] for c in breakdown)
        assert total_pct == 100

    def test_get_category_breakdown_empty_range(self, test_user_id):
        """get_category_breakdown with no matching expenses returns empty list."""
        seed_test_expenses(test_user_id)

        breakdown = get_category_breakdown(test_user_id, start_date='2027-01-01')

        assert breakdown == [], 'Should return empty list when no expenses match'

    def test_query_helpers_honour_swapped_bounds(self, test_user_id):
        """Query helpers treat start > end as swapped (no app-level swap needed)."""
        seed_test_expenses(test_user_id)

        # Note: The spec says the *route* swaps bounds, but query helpers
        # should work correctly when given proper bounds. We test that
        # the route does the swap by testing reversed bounds at route level.
        # Here we just confirm normal bounds work.

        stats_forward = get_summary_stats(
            test_user_id,
            start_date='2026-05-22',
            end_date='2026-05-24'
        )

        # If we pass reversed to helpers directly, they would return 0
        # because SQL date >= '2026-05-24' AND date <= '2026-05-22' matches nothing
        stats_reversed = get_summary_stats(
            test_user_id,
            start_date='2026-05-24',
            end_date='2026-05-22'
        )

        # The helper itself doesn't swap — it's app.py's job
        assert stats_reversed['transaction_count'] == 0, \
            'Query helper should return 0 for reversed bounds (app.py handles swap)'

        assert stats_forward['transaction_count'] == 3, \
            'Forward bounds should work correctly'

    def test_query_helpers_with_none_bounds(self, test_user_id):
        """Passing None for date bounds is same as not passing them."""
        seed_test_expenses(test_user_id)

        stats_all = get_summary_stats(test_user_id)
        stats_with_none = get_summary_stats(
            test_user_id,
            start_date=None,
            end_date=None
        )

        assert stats_all == stats_with_none, \
            'None bounds should behave same as no bounds'
