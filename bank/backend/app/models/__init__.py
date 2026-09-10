from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)  # nullable for Google-only accounts
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # user, admin
    # OAuth support
    google_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    auth_provider = db.Column(db.String(20), nullable=False, default="email")  # email, google
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime(timezone=True), nullable=True)
    lockout_until = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    account = db.relationship("Account", backref="user", uselist=False, lazy=True)
    transactions = db.relationship("Transaction", backref="user", lazy=True,
                                   foreign_keys="Transaction.user_id")
    login_attempts = db.relationship("LoginAttempt", backref="user", lazy=True)
    security_events = db.relationship("SecurityEvent", backref="user", lazy=True)
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)

    def to_dict(self, include_email=True):
        data = {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_locked": self.is_locked,
            "auth_provider": self.auth_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data["email"] = self.email
        return data


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), unique=True, nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    account_type = db.Column(db.String(20), nullable=False, default="checking")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "account_number": self.account_number,
            "balance": float(self.balance),
            "currency": self.currency,
            "account_type": self.account_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.id"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # transfer_in, transfer_out, deposit, withdrawal
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    status = db.Column(db.String(20), nullable=False, default="completed")  # pending, completed, failed
    description = db.Column(db.Text, nullable=True)
    recipient_account = db.Column(db.String(20), nullable=True)
    recipient_name = db.Column(db.String(160), nullable=True)
    reference = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_type": self.transaction_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "recipient_account": self.recipient_account,
            "recipient_name": self.recipient_name,
            "reference": self.reference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=False)
    source_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    failure_reason = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "success": self.success,
            "source_ip": self.source_ip,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SecurityEvent(db.Model):
    __tablename__ = "security_events"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    event_id = db.Column(db.String(36), unique=True, nullable=False, default=gen_uuid, index=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    username = db.Column(db.String(80), nullable=True)
    source_ip = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    endpoint = db.Column(db.String(255), nullable=True)
    http_method = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    metadata_json = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "username": self.username,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "http_method": self.http_method,
            "status": self.status,
            "metadata": self.metadata_json,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(36), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    source_ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "source_ip": self.source_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OTP(db.Model):
    """One-time password for email verification / password reset."""
    __tablename__ = "otp_codes"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_hash = db.Column(db.String(256), nullable=False)  # bcrypt hash of the OTP
    purpose = db.Column(db.String(20), nullable=False, default="password_reset")  # password_reset, email_verify
    attempts = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=5)
    is_used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "purpose": self.purpose,
            "attempts": self.attempts,
            "is_used": self.is_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
