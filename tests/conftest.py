"""Shared pytest fixtures for Spendly tests."""
import pytest
import tempfile
from pathlib import Path

from app import app as flask_app
from database import db as db_module
from database.db import init_db, create_user, get_db


@pytest.fixture
def app(monkeypatch):
    """Flask app configured for testing with an isolated temp DB."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Monkeypatch the DB_PATH before any imports use it
    monkeypatch.setattr(db_module, 'DB_PATH', Path(db_path))

    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
    })

    with flask_app.app_context():
        init_db()
        yield flask_app

    # Cleanup
    import os
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Test client that is already logged in as 'testuser'."""
    # Create a test user
    user_id = create_user('Test User', 'test@example.com', 'testpass123')
    assert user_id is not None, 'Failed to create test user'

    # Log in
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123',
    }, follow_redirects=False)

    assert response.status_code == 302, 'Login should redirect'

    return client


@pytest.fixture
def test_user_id(app):
    """Create a test user and return the user_id."""
    user_id = create_user('Test User', 'test@example.com', 'testpass123')
    assert user_id is not None
    return user_id
