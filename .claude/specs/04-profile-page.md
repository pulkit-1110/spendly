# Spec: Profile Page

## Overview

This step implements the `/profile` route, giving authenticated users a dedicated page
to view their account details (name, email, member-since date) and a high-level summary
of their spending activity (total expenses, total amount spent, most-used category).
The profile page is the first logged-in-only page in Spendly, so it also establishes
the `login_required` redirect pattern that later expense routes will reuse.

## Depends on

- Step 1 — Database Setup (users and expenses tables, `get_db()`)
- Step 2 — Registration (`create_user`, `users` table populated)
- Step 3 — Login and Logout (session set with `user_id` and `user_name`)

## Routes

- `GET /profile` — renders the profile page with user info and spending summary — **logged-in only** (redirect to `/login` if not authenticated)

## Database changes

No new tables or columns.

New helper function needed in `database/db.py`:

- `get_user_by_id(user_id)` — fetches a single user row by primary key (returns dict with `id`, `name`, `email`, `created_at`)
- `get_expense_summary(user_id)` — returns a dict with:
  - `total_count` — number of expenses for the user
  - `total_amount` — sum of all expense amounts (0.0 if none)
  - `top_category` — the category with the most entries (`None` if no expenses)

## Templates

- **Create:** `templates/profile.html` — profile page extending `base.html`
- **Modify:** `templates/base.html` — add a "Profile" link in the authenticated nav links (alongside the existing "Sign out" link)

## Files to change

- `app.py` — replace the stub `/profile` route with a real implementation
- `database/db.py` — add `get_user_by_id()` and `get_expense_summary()` helpers
- `templates/base.html` — add Profile nav link for authenticated users
- `static/css/style.css` — add `.profile-*` component styles

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw sqlite3 only
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug — never store or display plain-text passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Authentication guard: if `session.get("user_id")` is falsy, redirect to `/login` with a flashed message; do not use `abort()`
- DB helpers live in `database/db.py` only — the route function must not contain SQL
- The route function fetches user + summary, passes both to the template, and renders — one responsibility only

## Definition of done

- [ ] Visiting `/profile` while logged out redirects to `/login` and flashes "Please log in to view your profile."
- [ ] Visiting `/profile` while logged in renders `profile.html` without errors
- [ ] The page displays the logged-in user's name, email, and formatted `created_at` date
- [ ] The page displays the total number of expenses and total amount spent
- [ ] The page displays the top spending category (or a friendly "No expenses yet" message if empty)
- [ ] The navbar shows a "Profile" link for authenticated users that navigates to `/profile`
- [ ] All internal links use `url_for()` — no hardcoded paths
- [ ] The page is styled consistently with the rest of the app using CSS variables from `style.css`
- [ ] `pytest` passes with no regressions
