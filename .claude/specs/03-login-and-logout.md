# Spec: Login and Logout

## Overview

Implement login and logout functionality so registered users can authenticate into Spendly and maintain a session across requests. This step transforms the existing stub `/login` and `/logout` routes into a working session-based authentication system using Flask's built-in session cookie. After this step, the app can distinguish between anonymous and authenticated users, which is the foundation for all protected routes (profile, expenses) in later steps.

## Depends on

- Step 1: Database Setup — requires `get_db()` and the `users` table
- Step 2: Registration — requires `create_user()` and the `password_hash` column; a registered user is needed to test login

## Routes

- `POST /login` — process login form, verify credentials, set session — public
- `GET /logout` — clear session and redirect to landing page — public (no login required to call)

## Database changes

No database changes. The `users` table already has `id`, `email`, and `password_hash` columns needed for credential verification.

## Templates

- **Create:** None (`login.html` already exists as a stub)
- **Modify:**
  - `templates/login.html` — add login form with email + password fields, flash message display, and a link to `/register`
  - `templates/base.html` — add conditional nav links: show "Login / Register" when logged out, show "Logout" (and user name) when logged in

## Files to change

- `app.py` — implement `POST /login` handler and `GET /logout` handler; add `get_user_by_email()` import
- `database/db.py` — add `get_user_by_email(email)` helper
- `templates/login.html` — implement login form
- `templates/base.html` — add session-aware nav links

## Files to create

No new files needed.

## New dependencies

No new dependencies. Uses `werkzeug.security.check_password_hash` (already installed) and Flask's built-in `session`.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite queries only
- Parameterised queries only — never use f-strings or string formatting in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask's `session` dict to store the logged-in user's `id` and `name` — no JWT, no cookies by hand
- `SECRET_KEY` must already be set on the app (it is — `app.config['SECRET_KEY']`)
- After successful login redirect to `/` (landing) — not `/profile` (that is Step 4)
- After logout, redirect to `/` — clear the entire session with `session.clear()`
- Use `flash()` for login error messages — do not expose whether email or password was wrong (single generic message)
- Use `url_for()` for all internal links — never hardcode URLs
- Do not implement the "remember me" feature — that is out of scope

## Definition of done

- [ ] `GET /login` renders the login form with email and password fields
- [ ] `POST /login` with valid credentials sets `session['user_id']` and `session['user_name']` and redirects to `/`
- [ ] `POST /login` with wrong password shows a generic error message and does not log the user in
- [ ] `POST /login` with unknown email shows the same generic error message
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] After logout, visiting `/logout` again (already logged out) still redirects to `/` without error
- [ ] `base.html` nav shows "Login" and "Register" links when no session exists
- [ ] `base.html` nav shows the user's name and a "Logout" link when `session['user_id']` is set
- [ ] The demo user (`demo@spendly.com` / `demo123`) can log in successfully
- [ ] All SQL in `get_user_by_email()` uses parameterized queries
