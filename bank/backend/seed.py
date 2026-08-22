"""
Seed script to populate the database with demo data for the SecureBank Lab.
Run with: python seed.py
"""
import sys
import io

# Fix Windows console encoding for Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.app import create_app
from app.models import db, User, Account, Transaction, SecurityEvent, LoginAttempt, gen_uuid, utcnow
from app.auth import hash_password
from app.services.account_service import generate_account_number
from datetime import datetime, timezone, timedelta
import random
import uuid


def seed():
    app = create_app()
    with app.app_context():
        print("Seeding database...")

        # Clear existing data (order matters due to foreign keys)
        from app.models import AuditLog
        AuditLog.query.delete()
        SecurityEvent.query.delete()
        LoginAttempt.query.delete()
        Transaction.query.delete()
        Account.query.delete()
        User.query.delete()
        db.session.commit()

        # --- Admin user ---
        admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@securebank.lab",
            password_hash=hash_password("Admin@123"),
            first_name="System",
            last_name="Administrator",
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

        admin_account = Account(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            account_number=generate_account_number(),
            balance=100000.00,
            currency="USD",
            account_type="checking",
            status="active",
        )
        db.session.add(admin_account)
        db.session.commit()
        print("  [OK] Admin user created (admin / Admin@123)")

        # --- Demo users ---
        demo_users = [
            ("alice", "alice@securebank.lab", "Alice", "Johnson", "Alice@123", 7500.00),
            ("bob", "bob@securebank.lab", "Bob", "Smith", "Bob@123", 12345.67),
            ("charlie", "charlie@securebank.lab", "Charlie", "Brown", "Charlie@123", 500.00),
            ("diana", "diana@securebank.lab", "Diana", "Prince", "Diana@123", 25000.00),
            ("eve", "eve@securebank.lab", "Eve", "Williams", "Eve@123", 8750.25),
        ]

        users = []
        for uname, email, fname, lname, pwd, balance in demo_users:
            user = User(
                id=str(uuid.uuid4()),
                username=uname,
                email=email,
                password_hash=hash_password(pwd),
                first_name=fname,
                last_name=lname,
                role="user",
            )
            db.session.add(user)
            db.session.commit()
            users.append(user)

            account = Account(
                id=str(uuid.uuid4()),
                user_id=user.id,
                account_number=generate_account_number(),
                balance=balance,
                currency="USD",
                account_type="checking",
                status="active",
            )
            db.session.add(account)
            db.session.commit()
            print(f"  [OK] User created ({uname} / {pwd})")

        # --- Sample transactions ---
        now = utcnow()
        for user in users:
            account = Account.query.filter_by(user_id=user.id).first()
            num_transactions = random.randint(3, 8)
            for i in range(num_transactions):
                days_ago = random.randint(1, 30)
                amount = round(random.uniform(10, 500), 2)
                ttype = random.choice(["transfer_out", "transfer_in"])
                status = random.choice(["completed", "completed", "completed", "pending"])

                recipient_user = random.choice([u for u in users if u.id != user.id])
                recipient_acct = Account.query.filter_by(user_id=recipient_user.id).first()

                tx = Transaction(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    account_id=account.id,
                    transaction_type=ttype,
                    amount=amount,
                    currency="USD",
                    status=status,
                    description=random.choice([
                        "Groceries", "Electric bill", "Rent payment",
                        "Freelance work", "Dinner", "Online shopping",
                        "Gas station", "Coffee shop", "Transfer",
                    ]),
                    recipient_account=recipient_acct.account_number if recipient_acct else None,
                    recipient_name=f"{recipient_user.first_name} {recipient_user.last_name}" if recipient_acct else None,
                    reference=f"TXF-{str(uuid.uuid4())[:8].upper()}",
                    created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                db.session.add(tx)

            db.session.commit()
            print(f"  [OK] {num_transactions} transactions created for {user.username}")

        # --- Sample login history ---
        for user in users:
            for i in range(random.randint(2, 6)):
                days_ago = random.randint(0, 30)
                attempt = LoginAttempt(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    success=random.choice([True, True, True, False]),
                    source_ip=f"192.168.1.{random.randint(10, 250)}",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    failure_reason=random.choice([None, "invalid_credentials"]),
                    created_at=now - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                db.session.add(attempt)

            db.session.commit()

        # --- Sample security events ---
        event_types = [
            "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", "TRANSFER_CREATED",
            "PASSWORD_CHANGE", "ACCOUNT_CREATED",
        ]
        for user in users:
            for i in range(random.randint(2, 5)):
                days_ago = random.randint(0, 30)
                event = SecurityEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=now - timedelta(days=days_ago, hours=random.randint(0, 23)),
                    event_type=random.choice(event_types),
                    user_id=user.id,
                    username=user.username,
                    source_ip=f"192.168.1.{random.randint(10, 250)}",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    endpoint="/api/auth/login",
                    http_method="POST",
                    status=random.choice(["SUCCESS", "FAILED"]),
                    metadata_json={},
                )
                db.session.add(event)

            db.session.commit()

        print("\nSeed complete!")
        print("\n--- Test Credentials ---")
        print("  Admin:   admin / Admin@123")
        print("  Alice:   alice / Alice@123")
        print("  Bob:     bob / Bob@123")
        print("  Charlie: charlie / Charlie@123")
        print("  Diana:   diana / Diana@123")
        print("  Eve:     eve / Eve@123")


if __name__ == "__main__":
    seed()
