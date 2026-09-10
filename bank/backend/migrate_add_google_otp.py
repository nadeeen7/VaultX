#!/usr/bin/env python3
"""
One-time migration script to add Google OAuth and OTP support.

Run from the bank/backend directory:
    python migrate_add_google_otp.py

This script:
1. Adds google_id, auth_provider columns to users table
2. Makes password_hash nullable (for Google-only accounts)
3. Creates otp_codes table

Safe to run multiple times (idempotent).
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.models import db


def migrate():
    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        # Check if columns exist before adding
        inspector = db.inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("users")}

        if "google_id" not in columns:
            print("Adding google_id column to users...")
            db.session.execute(db.text(
                'ALTER TABLE users ADD COLUMN google_id VARCHAR(64) UNIQUE'
            ))
            db.session.commit()
            print("  ✓ google_id added")
        else:
            print("  ✓ google_id already exists")

        if "auth_provider" not in columns:
            print("Adding auth_provider column to users...")
            db.session.execute(db.text(
                "ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'email'"
            ))
            db.session.commit()
            print("  ✓ auth_provider added")
        else:
            print("  ✓ auth_provider already exists")

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
            print("  ✓ password_hash is now nullable")
        else:
            print("  ✓ password_hash is already nullable")

        # Create otp_codes table
        tables = {t for t in inspector.get_table_names()}
        if "otp_codes" not in tables:
            print("Creating otp_codes table...")
            OTP.__table__.create(db.engine)
            db.session.commit()
            print("  ✓ otp_codes table created")
        else:
            print("  ✓ otp_codes table already exists")

        # Create indexes
        print("Creating indexes...")
        try:
            db.session.execute(db.text(
                'CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)'
            ))
            db.session.execute(db.text(
                'CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_codes(email)'
            ))
            db.session.commit()
            print("  ✓ Indexes created")
        except Exception as e:
            print(f"  ⚠ Index creation skipped: {e}")

        print("\nMigration complete!")


# Need to import OTP model for table creation
from app.models import OTP

if __name__ == "__main__":
    migrate()
