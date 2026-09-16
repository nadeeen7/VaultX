#!/usr/bin/env python3
"""
Idempotent migration script to add email-delivery tracking to otp_codes.

Run from the bank/backend directory:
    python migrate_add_otp_delivered_at.py

Or pointing at any database (e.g. production) WITHOUT printing credentials:
    set DATABASE_URL=...   (Windows)   |   export DATABASE_URL=...   (macOS/Linux)
    python migrate_add_otp_delivered_at.py

This script:
1. Creates the otp_codes table if it does not exist yet (via db.create_all)
2. Adds the delivered_at column to otp_codes if it is missing

Why: the forgot-password rate limit only counts OTPs that were actually
delivered by email (delivered_at IS NOT NULL), so a failed SMTP send never
blocks the user from retrying. Existing rows get delivered_at = NULL, which
is correct: those OTPs were created before delivery tracking existed.

Safe to run multiple times (idempotent). No existing rows are modified or
deleted — only additive ALTERs and CREATEs are used.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app.app import create_app
from app.models import db


def migrate():
    """Run the idempotent otp_codes.delivered_at migration."""
    # DATABASE_URL must come from the environment (local .env or shell export).
    # It is never printed.
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        print("Set it in your shell or bank/backend/.env (value is kept secret):")
        print("  Windows PowerShell:  $env:DATABASE_URL = \"<your-url>\"")
        print("  macOS/Linux:         export DATABASE_URL=\"<your-url>\"")
        sys.exit(1)

    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        engine = db.engine

        # Ensure the table exists first (create_all is idempotent).
        db.create_all()

        inspector = db.inspect(engine)
        if "otp_codes" not in set(inspector.get_table_names()):
            print("ERROR: otp_codes table still missing after create_all.")
            sys.exit(2)

        columns = {c["name"] for c in inspector.get_columns("otp_codes")}

        if "delivered_at" not in columns:
            print("Adding delivered_at column to otp_codes...")
            db.session.execute(db.text(
                'ALTER TABLE otp_codes ADD COLUMN delivered_at TIMESTAMP WITH TIME ZONE'
            ))
            db.session.commit()
            print("  [OK] delivered_at added")
        else:
            print("  [OK] delivered_at already exists")

        # Final verification — confirm the column now exists so the
        # forgot-password query cannot hit UndefinedColumn at runtime.
        inspector = db.inspect(engine)
        final_columns = {c["name"] for c in inspector.get_columns("otp_codes")}
        if "delivered_at" not in final_columns:
            print("\n[FAIL] VERIFICATION FAILED - delivered_at column is still missing")
            sys.exit(2)

        print("\nVerification: otp_codes.delivered_at exists.")
        print("Forgot-password delivery tracking queries will no longer raise UndefinedColumn.")
        print("\nMigration complete! (No existing rows were modified or deleted.)")


if __name__ == "__main__":
    migrate()
