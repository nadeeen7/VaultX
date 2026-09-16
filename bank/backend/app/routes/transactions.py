from flask import Blueprint, request, jsonify, g
from app.models import db, Transaction
from app.auth import token_required
from app.services.account_service import process_transfer
from app.services.validation import get_json_object, clean_string
from app.logging.security_logger import log_security_event, log_audit

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


@transactions_bp.route("/transfer", methods=["POST"])
@token_required
def create_transfer():
    """Create a new money transfer."""
    user = g.current_user
    data, err = get_json_object()
    if err:
        return err

    required = ["recipient_account", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate account identifier (system-generated format: VB + 10 digits)
    recipient_account = clean_string(data["recipient_account"], 20)
    if not recipient_account or len(recipient_account) > 20:
        return jsonify({"error": "Invalid recipient account"}), 400

    # Free-text fields: hard length caps (stored as text, rendered as text)
    recipient_name = clean_string(data.get("recipient_name", "Unknown"), 160) or "Unknown"
    description = clean_string(data.get("description", "Transfer"), 255) or "Transfer"

    try:
        amount = float(data["amount"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    if amount > 100000:
        return jsonify({"error": "Transfer amount exceeds limit of $100,000"}), 400

    try:
        transaction = process_transfer(
            user=user,
            amount=amount,
            recipient_account=recipient_account,
            recipient_name=recipient_name,
            description=description,
        )

        log_security_event(
            event_type="TRANSFER_CREATED",
            user_id=user.id,
            username=user.username,
            status="SUCCESS",
            metadata={
                "transaction_id": transaction.id,
                "amount": amount,
                "recipient_account": recipient_account,
                "reference": transaction.reference,
            },
        )
        log_audit(
            action="CREATE",
            resource_type="transaction",
            resource_id=transaction.id,
            user_id=user.id,
            details={
                "amount": amount,
                "recipient": recipient_account,
            },
        )

        return jsonify({
            "message": "Transfer completed successfully",
            "transaction": transaction.to_dict(),
        }), 201

    except ValueError as e:
        log_security_event(
            event_type="TRANSFER_FAILED",
            user_id=user.id,
            username=user.username,
            status="FAILED",
            metadata={
                "amount": amount,
                "recipient_account": recipient_account,
                "reason": str(e),
            },
        )
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        log_security_event(
            event_type="TRANSFER_FAILED",
            user_id=user.id,
            username=user.username,
            status="FAILED",
            metadata={"reason": type(e).__name__},
        )
        return jsonify({"error": "Transfer failed"}), 500
