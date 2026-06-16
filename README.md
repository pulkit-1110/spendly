# Spendly

A lightweight personal **expense tracker** built with Flask and SQLite. Spendly lets you
register an account, log daily expenses across common categories, edit or delete them, and
review your spending through a simple analytics view — all in a clean, server-rendered web app
with no frontend framework.

## Features

- **User accounts** — register, log in, and log out with secure, hashed passwords (Werkzeug) and
session-based authentication.
- **Expense tracking** — add, edit, and delete expenses, each with an amount, category, date, and
optional description.
- **Categories** — Food, Transport, Bills, Health, Entertainment, Shopping, and Other.
- **Profile** — view your account details and filter your expenses by date range.
- **Analytics** — review spending summaries across your expenses.
- **Static pages** — landing, terms, and privacy pages.

## Tech Stack

- **Backend:** Python 3.10+, Flask 3
- **Database:** SQLite (standard library `sqlite3`, parameterized queries, manual foreign-key enforcement)
- **Frontend:** Jinja2 templates + vanilla JavaScript and CSS (no React/jQuery/npm)
- **Auth:** Werkzeug password hashing + Flask sessions
- **Server:** Gunicorn (via `Procfile`) for production

## Project Structure

```
spendly/
├── app.py                # All Flask routes (single file, no blueprints)
├── database/
│   ├── db.py             # SQLite connection, schema init, and demo seeding
│   └── queries.py        # Read/aggregate query helpers (profile, analytics, filters)
├── templates/            # Jinja2 templates — every page extends base.html
│   ├── base.html
│   ├── landing.html
│   ├── register.html  login.html  profile.html
│   ├── add_expense.html  edit_expense.html  analytics.html
│   └── terms.html  privacy.html
├── static/
│   ├── css/style.css     # Global styles
│   └── js/main.js        # Vanilla JS
├── tests/                # pytest suite (add/edit/delete expense, profile filters)
├── requirements.txt
└── Procfile              # gunicorn entrypoint for deployment
```

## Getting Started

### Prerequisites

- Python 3.10 or newer

### Setup

```bash
# Clone the repository
git clone https://github.com/pulkit-1110/spendly.git
cd spendly

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the development server

```bash
python app.py
```

The app runs at **http://localhost:5001** (port 5001, not the Flask default 5000).

### Demo account

The database can be seeded with a demo user and sample expenses:

- **Email:** `demo@spendly.com`
- **Password:** `demo123`

## Routes

| Route                          | Method     | Description                              |
| ------------------------------ | ---------- | ---------------------------------------- |
| `/`                            | GET        | Landing page                             |
| `/register`                    | GET, POST  | Create a new account                     |
| `/login`                       | GET, POST  | Log in                                   |
| `/logout`                      | GET        | Log out and clear the session            |
| `/profile`                     | GET        | Account details + date-filtered expenses |
| `/analytics`                   | GET        | Spending analytics                       |
| `/expenses/add`                | GET, POST  | Add an expense                           |
| `/expenses/<id>/edit`          | GET, POST  | Edit an expense                          |
| `/expenses/<id>/delete`        | POST       | Delete an expense                        |
| `/terms`, `/privacy`           | GET        | Static legal pages                       |

## Testing

```bash
# Run the full suite
pytest

# Run a specific test file
pytest tests/test_add_expense.py

# Run a single test by name, with output
pytest -k "test_name" -s
```

## Deployment

A `Procfile` is included for platforms like Render/Railway/Heroku:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

> **Note:** `app.config['SECRET_KEY']` is set to a development placeholder. Set a strong,
> secret value (e.g. via an environment variable) before deploying to production.

## License

  MIT License

  Copyright (c) 2026 Pulkit Uppal

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
