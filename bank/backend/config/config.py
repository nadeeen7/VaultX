import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _require_ssl_if_missing(database_uri: str) -> str:
    """
    Return a DATABASE_URL that requests TLS, without touching credentials.

    - An sslmode already present in the URL is preserved untouched.
    - Otherwise sslmode=require is appended (Render PostgreSQL always supports
      SSL; 'require' keeps traffic encrypted without cert-verification
      pitfalls, and never appears in logs).
    """
    if "sslmode=" in database_uri:
        return database_uri
    separator = "&" if "?" in database_uri else "?"
    return f"{database_uri}{separator}sslmode=require"


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    _raw_database_uri = os.getenv(
        "DATABASE_URL",
        "postgresql://vaultx:vaultx@localhost:5432/vaultx_bank"
    )
    # In production (Render), require TLS unless DATABASE_URL already sets an
    # sslmode. Never applied outside production so local dev is unaffected.
    SQLALCHEMY_DATABASE_URI = (
        _require_ssl_if_missing(_raw_database_uri)
        if os.getenv("FLASK_ENV") == "production" else _raw_database_uri
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Production-safe connection pooling (Render PostgreSQL) ─────────
    # Render's Postgres sits behind a load balancer that silently drops idle
    # TCP connections. A pooled connection that sat idle longer than that is
    # dead, and the next query dies with:
    #   psycopg2.OperationalError: consuming input failed:
    #   SSL error: unexpected eof while reading
    # Defenses (engine options only — no credentials involved):
    #   pool_pre_ping  : ping every pooled connection on checkout; stale ones
    #                    are transparently discarded and replaced, so requests
    #                    no longer fail on dead pooled connections.
    #   pool_recycle   : proactively replace connections older than 5 minutes,
    #                    well under the longest provider idle cutoff.
    #   pool_timeout   : fail fast (after 30s) instead of hanging if the pool
    #                    is exhausted.
    # Connect-time SSL is enforced via DATABASE_URL's sslmode (see above).
    # connect_timeout is PostgreSQL-specific, so it is only applied when the
    # configured URI actually points at PostgreSQL (keeps SQLite tests valid).
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "280")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "3")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
        "connect_args": (
            {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10"))}
            if SQLALCHEMY_DATABASE_URI.startswith("postgresql") else {}
        ),
    }

    # CORS: comma-separated list of allowed frontend origins.
    # In development, defaults to localhost. In production, must be set explicitly.
    _cors_raw = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else []

    # Security settings
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Set TRUST_PROXY=true in production (Render sits behind a reverse proxy,
    # so remote_addr is the proxy and real client IPs come from X-Forwarded-For).
    # Leave unset in local dev so spoofed X-Forwarded-For headers are ignored.
    TRUST_PROXY = os.getenv("TRUST_PROXY", "").strip().lower() in ("1", "true", "yes", "on")

    # Rate limiting for auth endpoints (per identifier+IP per window).
    # Per-process limits; with 2 gunicorn workers effective limits double.
    RATE_LIMIT_LOGIN = int(os.getenv("RATE_LIMIT_LOGIN", "10"))
    RATE_LIMIT_REGISTER = int(os.getenv("RATE_LIMIT_REGISTER", "10"))
    RATE_LIMIT_GOOGLE = int(os.getenv("RATE_LIMIT_GOOGLE", "15"))
    RATE_LIMIT_FORGOT_PASSWORD = int(os.getenv("RATE_LIMIT_FORGOT_PASSWORD", "5"))
    RATE_LIMIT_OTP = int(os.getenv("RATE_LIMIT_OTP", "10"))

    # SIEM integration settings (optional — Bank works fine without SIEM)
    SIEM_API_URL = os.getenv("SIEM_API_URL", "")
    SIEM_API_KEY = os.getenv("SIEM_API_KEY", "")

    # Google OAuth (optional — Google Sign-In won't work without this)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Email / SMTP (optional — Forgot Password emails won't send without this)
    # NOTE: values are read via _mail_env() to strip accidental leading/trailing
    # whitespace (a common cause of SMTP auth failures when pasting secrets
    # into Render). Only whitespace is trimmed — values are never logged.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "").strip()
    try:
        MAIL_PORT = int((os.getenv("MAIL_PORT", "") or "587").strip())
    except (TypeError, ValueError):
        MAIL_PORT = 587
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip()
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "").strip()
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "").strip()

    # Frontend URL for email links
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class DevelopmentConfig(Config):
    DEBUG = True

    # Development defaults: allow localhost origins if none configured
    _cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]

    # Development defaults: SIEM points to local instance if not configured
    SIEM_API_URL = os.getenv("SIEM_API_URL", "http://localhost:5001")
    SIEM_API_KEY = os.getenv("SIEM_API_KEY", "vaultx_siem_api_key_2026")


class ProductionConfig(Config):
    DEBUG = False

    # Production Postgres: with 2 gunicorn workers this keeps each worker's
    # pool at ≤8 connections (3 base + 5 overflow) — comfortably within Render
    # connection limits while leaving headroom for the SIEM backend's pool.
    # Production always targets PostgreSQL (Render), so connect_timeout applies.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "280")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "3")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
        "connect_args": {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10"))},
    }


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
