#!/usr/bin/env python3
"""
Idempotent migration for the security-event severity/target columns.

Run from the bank/backend directory:
    python migrate_add_severity_target.py

Adds nullable severity and target columns to security_events if missing.
Existing rows are never modified or deleted (they keep severity/target NULL,
which is valid). Safe to run multiple times.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app.app import create_app
from app.models import db


def migrate():
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        print("Set it in your shell or bank/backend/.env (value is kept secret).")
        sys.exit(1)

    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        engine = db.engine
        db.create_all()

        inspector = db.inspect(engine)
        if "security_events" not in set(inspector.get_table_names()):
            print("ERROR: security_events table missing after create_all.")
            sys.exit(2)

        columns = {c["name"] for c in inspector.get_columns("security_events")}

        if "severity" not in columns:
            print("Adding severity column to security_events...")
            db.session.execute(db.text(
                'ALTER TABLE security_events ADD COLUMN severity VARCHAR(10)'
            ))
            db.session.commit()
            print("  [OK] severity added")
        else:
            print("  [OK] severity already exists")

        if "target" not in columns:
            print("Adding target column to security_events...")
            db.session.execute(db.text(
                'ALTER TABLE security_events ADD COLUMN target VARCHAR(50)'
            ))
            db.session.commit()
            print("  [OK] target added")
        else:
            print("  [OK] target already exists")

        # Verify
        inspector = db.inspect(engine)
        final = {c["name"] for c in inspector.get_columns("security_events")}
        missing = [c for c in ("severity", "target") if c not in final]
        if missing:
            print(f"\n[FAIL] VERIFICATION FAILED - still missing: {missing}")
            sys.exit(2)
        print("\nVerification: security_events.severity and security_events.target exist.")
        print("Migration complete! (No existing rows were modified or deleted.)")


if __name__ == "__main__":
    migrate()
