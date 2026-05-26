# Spec: Registration

## Overview

Implement user registration functionality to allow new users to create accounts in the Spendly expense tracker. This transforms the existing stub `/register` route into a fully functional registration system with form handling, validation, password hashing, and database storage.

## Depends on

- Step 1: Database Setup — requires users table and database helper functions

## Routes

- `POST /register` — process registration form submission — public

## Database changes

No database changes. The users table from Step 1 already supports registration with the required columns: id, name, email, password_hash, created_at.

## Templates

- **Create:** None (register.html already exists)
- **Modify:** 
  - `templates/register.html` — add form with proper validation and error display
  - `templates/base.html` — ensure flash message display is working

## Files to change

- `app.py` — add POST /register route handler with form processing
- `database/db.py` — add user creation helper function
- `templates/register.html` — implement registration form
- `templates/base.html` — ensure flash messages display properly (if not already implemented)

## Files to create

No new files needed.

## New dependencies

No new dependencies. Uses existing Flask, werkzeug, and sqlite3 functionality.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw SQLite queries only
- Parameterised queries only — never use f-strings or string formatting in SQL
- Passwords hashed with werkzeug.security.generate_password_hash
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask's flash() for user feedback messages
- Redirect to login page after successful registration
- Proper form validation on both client and server side
- Handle duplicate email gracefully with user-friendly error message
- Use url_for() for all internal links — never hardcode URLs

## Definition of done

- [ ] GET /register displays registration form with name, email, password, and confirm password fields
- [ ] POST /register creates new user account when valid data is submitted
- [ ] Password is properly hashed before database storage
- [ ] Duplicate email registration shows error message without crashing
- [ ] Empty or invalid fields show appropriate validation messages
- [ ] Password confirmation must match main password field
- [ ] Successful registration redirects to login page with success message
- [ ] Registration form includes CSRF protection (Flask-WTF or manual token)
- [ ] Form styling is consistent with existing landing page design
- [ ] All database operations use parameterized queries
- [ ] Server-side validation prevents SQL injection and XSS attacks