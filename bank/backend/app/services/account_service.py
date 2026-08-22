import random
from app.models import db, User, Account, Transaction, gen_uuid


def generate_account_number() -> str:
    """Generate a unique fake account number."""
    while True:
        number = f"VB{random.randint(1000000000, 9999999999)}"
        if not Account.query.filter_by(account_number=number).first():
            return number


def create_account_for_user(user_id: str, initial_balance: float = 5000.00) -> Account:
    """Create a checking account for a new user with an initial balance."""
    account = Account(
        id=gen_uuid(),
        user_id=user_id,
        account_number=generate_account_number(),
        balance=initial_balance,
        currency="USD",
        account_type="checking",
        status="active",
    )
    db.session.add(account)
    db.session.commit()
    return account


def process_transfer(user: User, amount: float, recipient_account: str,
                     recipient_name: str, description: str = None) -> Transaction:
    """
    Process a money transfer from the user's account.
    Returns the Transaction object with status set.
    """
    account = Account.query.filter_by(user_id=user.id).first()
    if not account:
        raise ValueError("Account not found")

    if account.status != "active":
        raise ValueError("Account is not active")

    if amount <= 0:
        raise ValueError("Amount must be positive")

    if float(account.balance) < amount:
        # Log failed transfer
        transaction = Transaction(
            id=gen_uuid(),
            user_id=user.id,
            account_id=account.id,
            transaction_type="transfer_out",
            amount=amount,
            currency="USD",
            status="failed",
            description=description or "Transfer",
            recipient_account=recipient_account,
            recipient_name=recipient_name,
            reference=f"TXF-{gen_uuid()[:8].upper()}",
        )
        db.session.add(transaction)
        db.session.commit()
        raise ValueError("Insufficient funds")

    # Create outgoing transaction
    reference = f"TXF-{gen_uuid()[:8].upper()}"
    transaction = Transaction(
        id=gen_uuid(),
        user_id=user.id,
        account_id=account.id,
        transaction_type="transfer_out",
        amount=amount,
        currency="USD",
        status="completed",
        description=description or "Transfer",
        recipient_account=recipient_account,
        recipient_name=recipient_name,
        reference=reference,
    )
    db.session.add(transaction)

    # Deduct from balance
    account.balance = float(account.balance) - amount
    db.session.commit()

    return transaction
