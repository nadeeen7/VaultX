"""
Pytest fixtures + shared helpers for the VaultX Bank regression/security suite.

Isolation guarantees:
- Uses a throwaway SQLite file database (never the real DATABASE_URL / Postgres).
- SMTP sends are mocked per-test (no real email is sent).
- SIEM push points at a closed local port, so background pushes fail fast and
  silently (exercises the "SIEM offline" path).
- TRUST_PROXY is unset so proxy-header spoofing paths stay inert.

The production database is NEVER touched by this suite.
"""
import os
import sys

import pytest

# Make `bank/backend` importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test-only environment: fake values, no real secrets. Set BEFORE importing config.
os.environ["SIEM_API_URL"] = "http://127.0.0.1:1"  # closed port -> instant refuse
os.environ["SIEM_API_KEY"] = "test-siem-key"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-secret"
os.environ["MAIL_SERVER"] = "smtp.test.local"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_USERNAME"] = "test@vaultx.test"
os.environ["MAIL_PASSWORD"] = "test-password-not-real"
os.environ["MAIL_DEFAULT_SENDER"] = "test@vaultx.test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-not-real"
os.environ.pop("TRUST_PROXY", None)          # keep spoofing paths inert
os.environ.pop("CORS_ORIGINS", None)         # use development localhost default
os.environ["FLASK_ENV"] = "test"

from config.config import config_by_name  # noqa: E402
from app.app import create_app  # noqa: E402
from app.models import db as _db, User  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.services.account_service import create_account_for_user  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(__file__), "vaultx_test.db")


class TestConfig(config_by_name["development"]):
    """Development config, isolated onto a throwaway SQLite file."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_PATH


config_by_name["test"] = TestConfig


@pytest.fixture(scope="session")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    application = create_app("test")
    yield application
    # Dispose pooled connections so Windows releases the file lock.
    with application.app_context():
        _db.engine.dispose()
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass  # best-effort cleanup on Windows


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    """App-context DB session for direct model assertions."""
    with app.app_context():
        yield _db.session


# ── Shared helpers ──────────────────────────────────────────────────────
VALID_PASSWORD = "Str0ngPass!"


def register_payload(username, email, password=VALID_PASSWORD):
    return {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password,
        "first_name": "Test",
        "last_name": "User",
    }


def login_payload(identifier, password=VALID_PASSWORD):
    return {"email": identifier, "password": password}


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def make_user(db_session, username, email, password="OldPassword123", google=False):
    """Create a user + bank account directly (bypasses register rate limit)."""
    u = User(
        username=username,
        email=email,
        password_hash=None if google else hash_password(password),
        first_name="Test", last_name="User", role="user",
        auth_provider="google" if google else "email",
        google_id=f"gid-{username}" if google else None,
    )
    db_session.add(u)
    db_session.commit()
    create_account_for_user(u.id, initial_balance=5000.00)
    return u


def capture_otp(client, email, monkeypatch):
    """Request a password-reset OTP for an existing user and capture the code.

    The email service is mocked, so no real email is sent. Returns the 6-digit
    code (kept in a local variable only — never logged or persisted).
    """
    from app.routes import auth as auth_routes

    captured = {}

    def fake_send(email_addr, otp_code, purpose="password_reset"):
        captured["otp"] = otp_code
        return True, None

    monkeypatch.setattr(auth_routes, "send_otp_email", fake_send)
    resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    return captured["otp"]
