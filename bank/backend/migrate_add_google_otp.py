#!/usr/bin/env python3
"""
Idempotent migration script to add Google OAuth and OTP support.

Run from the bank/backend directory:
    python migrate_add_google_otp.py

Or pointing at any database (e.g. production) WITHOUT printing credentials:
    set DATABASE_URL=...   (Windows)   |   export DATABASE_URL=...   (macOS/Linux)
    python migrate_add_google_otp.py

This script:
1. Adds google_id, auth_provider columns to users table
2. Makes password_hash nullable (for Google-only accounts)
3. Creates otp_codes table
4. Creates supporting indexes

Safe to run multiple times (idempotent): every step first checks whether the
column/table/index already exists. No existing rows are ever modified or
deleted — only additive ALTERs and CREATEs are used.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app.app import create_app
from app.models import db, OTP


def migrate():
    """Run the idempotent Google/OTP schema migration."""
    # DATABASE_URL must come from the environment (local .env or shell export).
    # It is never printed. The app factory reads it via config.py.
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        print("Set it in your shell or bank/backend/.env (value is kept secret):")
        print("  Windows PowerShell:  $env:DATABASE_URL = \"<your-url>\"")
        print("  macOS/Linux:         export DATABASE_URL=\"<your-url>\"")
        sys.exit(1)

    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        engine = db.engine
        inspector = db.inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("users")}

        if "google_id" not in columns:
            print("Adding google_id column to users...")
            db.session.execute(db.text(
                'ALTER TABLE users ADD COLUMN google_id VARCHAR(64) UNIQUE'
            ))
            db.session.commit()
            print("  [OK] google_id added")
        else:
            print("  [OK] google_id already exists")

        if "auth_provider" not in columns:
            print("Adding auth_provider column to users...")
            db.session.execute(db.text(
                "ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'email'"
            ))
            db.session.commit()
            print("  [OK] auth_provider added")
        else:
            print("  [OK] auth_provider already exists")

        # Make password_hash nullable for Google-only accounts
        # This uses PostgreSQL syntax — adjust if using a different database
        print("Checking password_hash nullable constraint...")
        col_info = None
        for c in inspector.get_columns("users"):
            if c["name"] == "password_hash":
                col_info = c
                break

        if col_info and col_info.get("nullable") is False:
            print("Making password_hash nullable...")
            db.session.execute(db.text(
                'ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL'
            ))
            db.session.commit()
            print("  [OK] password_hash is now nullable")
        else:
            print("  [OK] password_hash is already nullable")

        # Create otp_codes table
        tables = {t for t in inspector.get_table_names()}
        if "otp_codes" not in tables:
            print("Creating otp_codes table...")
            OTP.__table__.create(engine)
            db.session.commit()
            print("  [OK] otp_codes table created")
        else:
            print("  [OK] otp_codes table already exists")

        # Create indexes (IF NOT EXISTS makes this idempotent)
        print("Creating indexes...")
        try:
            db.session.execute(db.text(
                'CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)'
            ))
            db.session.execute(db.text(
                'CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_codes(email)'
            ))
            db.session.commit()
            print("  [OK] Indexes created")
        except Exception as e:
            print(f"  [WARN] Index creation skipped: {type(e).__name__}")

        # Final verification — confirm the target columns now exist so the
        # Google auth queries cannot hit UndefinedColumn at runtime.
        inspector = db.inspect(engine)
        final_columns = {c["name"] for c in inspector.get_columns("users")}
        missing = [c for c in ("google_id", "auth_provider") if c not in final_columns]
        if missing:
            print(f"\n[FAIL] VERIFICATION FAILED - still missing columns: {missing}")
            sys.exit(2)
        print("\nVerification: users.google_id and users.auth_provider exist.")
        print("Google authentication queries will no longer raise UndefinedColumn.")
        print("\nMigration complete! (No existing rows were modified or deleted.)")


if __name__ == "__main__":
    migrate()
