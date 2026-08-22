from flask import Blueprint, request, jsonify, g
from app.models import db, Transaction
from app.auth import token_required
from app.services.account_service import process_transfer
from app.logging.security_logger import log_security_event, log_audit

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


@transactions_bp.route("/transfer", methods=["POST"])
@token_required
def create_transfer():
    """Create a new money transfer."""
    user = g.current_user
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ["recipient_account", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

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
            recipient_account=data["recipient_account"],
            recipient_name=data.get("recipient_name", "Unknown"),
            description=data.get("description", "Transfer"),
        )

        log_security_event(
            event_type="TRANSFER_CREATED",
            user_id=user.id,
            username=user.username,
            status="SUCCESS",
            metadata={
                "transaction_id": transaction.id,
                "amount": amount,
                "recipient_account": data["recipient_account"],
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
                "recipient": data["recipient_account"],
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
                "recipient_account": data["recipient_account"],
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
            metadata={"reason": str(e)},
        )
        return jsonify({"error": "Transfer failed"}), 500
