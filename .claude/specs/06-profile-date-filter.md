# Spec: Date Filter for Profile Page

## Overview

Add a date-range filter to the profile page so a logged-in user can
narrow the summary stats, recent transactions, and category breakdown
to expenses falling between an optional `start_date` and `end_date`.
Today the profile page renders all-time numbers from
`get_summary_stats`, `get_recent_transactions`, and
`get_category_breakdown` — there is no way for a user to ask "what did I
spend last month?" or "how much went to Food in Q1?". This step bridges
the gap between the profile-backend-routes step (Step 5, where live
queries were wired up) and the expense-add step (Step 7, where users
will start writing data the filter will become more useful for).

## Depends on

- Step 4 — Profile page (template, layout, CSS classes)
- Step 5 — Profile backend routes (the three query functions in
  `database/queries.py` that this filter will extend)

## Routes

- `GET /profile` — extended (not new) — accepts optional
  `start_date` and `end_date` query parameters (ISO format
  `YYYY-MM-DD`); access level: logged-in only (existing behaviour).

No new routes are added.

## Database changes

No schema changes. The `expenses.date` column is already TEXT in
`YYYY-MM-DD` format, which sorts and compares correctly with string
inequality operators in SQLite. The three query functions in
`database/queries.py` will be modified to accept optional
`start_date` and `end_date` arguments and add `AND date >= ?` /
`AND date <= ?` clauses to their existing `WHERE user_id = ?` filters.

## Templates

- **Create:** none.
- **Modify:**
  - `templates/profile.html` — add a date-range filter form above
    the summary card. Form uses `method="get"` and submits to
    `url_for('profile')` with `start_date` and `end_date` inputs of
    `type="date"`. Include a "Clear" link that points at
    `url_for('profile')` with no query string. Pre-populate the inputs
    with the currently active filter values when present. When a filter
    is active, show a small "Showing DD MMM YYYY – DD MMM YYYY" label
    near the summary heading.

## Files to change

- `app.py` — read `start_date` and `end_date` from `request.args` in
  the `profile` view, validate them, and pass them through to the
  three query functions. Pass the (validated, normalised) values back
  to the template so the form can re-render them.
- `database/queries.py` — extend `get_summary_stats`,
  `get_recent_transactions`, and `get_category_breakdown` to accept
  optional `start_date=None`, `end_date=None` keyword arguments and
  apply the corresponding SQL predicates only when the values are
  present.
- `templates/profile.html` — add the filter form and the active-range
  label as described above.
- `static/css/style.css` — add styles for the new
  `.profile-filter-*` classes (form layout, inputs, submit button,
  clear link, active-range label). Use existing CSS variables only.

## Files to create

- `.claude/specs/06-profile-date-filter.md` — this spec (already
  being created by the workflow).

No new Python, HTML, CSS, or JS files.

## New dependencies

No new dependencies. `datetime` from the standard library is already
imported in `database/queries.py` and is sufficient for validating
the ISO date strings.

## Rules for implementation

- No SQLAlchemy or ORMs — continue using raw `sqlite3` via `get_db()`.
- Parameterised queries only — use `?` placeholders for the new
  `start_date` and `end_date` predicates; never f-string them in.
- Passwords hashed with werkzeug — N/A for this step but still in force.
- Use CSS variables — never hardcode hex values; reuse `--ink`,
  `--ink-soft`, `--accent`, `--border`, `--paper-card`, `--radius-md`,
  etc.
- All templates extend `base.html` — `profile.html` already does.
- Validate `start_date` and `end_date` with
  `datetime.strptime(value, "%Y-%m-%d")`. If a value is malformed,
  treat it as not provided (silently drop it) — do not 500 and do not
  flash an error for this iteration; the `<input type="date">` already
  guards against bad input from the form.
- If `start_date > end_date` after parsing, swap them so the query is
  still meaningful rather than returning an empty set surprisingly.
- Filter values must propagate to all three queries so the summary,
  transaction list, and category breakdown stay consistent with each
  other (no mismatch between cards).
- Do not introduce a JS framework. The form is a plain GET submission;
  no JavaScript is required for this step.
- Keep DB logic in `database/queries.py` — do not write SQL in
  `app.py` or in the template.
- Use `url_for('profile')` for both the form `action` and the Clear
  link — never hardcode `/profile`.

## Definition of done

A reviewer can verify each item by running `python app.py` and
exercising the profile page in a browser:

1. Visiting `/profile` with no query string still renders the existing
   all-time stats, transactions, and category breakdown unchanged
   (regression check against Step 5's definition of done — seed user
   shows ₹346.24 spent, 8 transactions, "Bills" as top category).
2. The profile page shows a date-range filter form above the summary
   card with two `<input type="date">` fields labelled
   "From" and "To", a submit button, and a "Clear" link.
3. Submitting the form navigates to
   `/profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (GET, not
   POST) and the URL is shareable.
4. With a non-empty filter, the summary card's transaction count,
   total spent, and top category all reflect only expenses inside the
   range. The recent-transactions list shows only in-range rows. The
   category breakdown percentages recompute against the filtered
   total and still sum to exactly 100.
5. With only `start_date` set, the page shows everything from that
   date onward. With only `end_date` set, the page shows everything
   up to and including that date.
6. Setting `start_date` later than `end_date` does not error — the
   page renders the same range as if the values were swapped.
7. A malformed `start_date` or `end_date` (e.g. typed manually into
   the URL bar as `start_date=not-a-date`) is silently ignored; the
   page renders as if that bound were absent and does not 500.
8. Clicking "Clear" returns to `/profile` with an empty query string
   and resets the view to all-time data.
9. When a filter is active, the summary card shows a
   "Showing DD MMM YYYY – DD MMM YYYY" label so the user can see at
   a glance what they're looking at.
10. The filter form inputs are pre-populated with the currently
    active range when the page is reloaded, so the user can adjust
    rather than re-enter dates.
11. Visiting `/profile` while logged out still redirects to `/login`
    (auth behaviour unchanged).
12. No new pip packages were added; `requirements.txt` is untouched.
