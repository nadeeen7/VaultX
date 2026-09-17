import os
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests as http_requests

# Redact anything that looks like a credential inside exception text:
# "AUTHENTICATE PLAIN <b64>", "User ... <token>", long base64/hex-ish chunks,
# and anything following "password", "token", or "auth".
_B64_RE = re.compile(r"[A-Za-z0-9+/=_-]{16,}")
_SECRET_WORD_RE = re.compile(
    r"(?i)(password|passwd|token|auth\w*)\s*[:=]?\s*\S+"
)

# HTTP email APIs (port 443) used when outbound SMTP is unreachable —
# e.g. Render, where connecting to smtp.gmail.com:587 fails with
# "OSError: [Errno 101] Network is unreachable".
_API_PROVIDERS = ("resend", "brevo", "sendgrid")
_API_KEY_VAR = {
    "resend": "RESEND_API_KEY",
    "brevo": "BREVO_API_KEY",
    "sendgrid": "SENDGRID_API_KEY",
}


def _sanitize_exception(e: Exception) -> str:
    """
    Return a short, safe exception description for logging.
    Never include SMTP credentials, passwords, or OTP values.
    """
    parts = [type(e).__name__]
    message = " ".join(str(e).split())
    if message:
        message = _SECRET_WORD_RE.sub(lambda m: m.group(1) + ": [REDACTED]", message)
        message = _B64_RE.sub("[REDACTED]", message)
        parts.append(message[:200])
    return ": ".join(parts)


def _missing_mail_vars() -> list:
    """
    Return the NAMES of required SMTP mail environment variables that are
    missing. Never returns or logs any variable VALUES.
    """
    missing = []
    if not os.getenv("MAIL_SERVER"):
        missing.append("MAIL_SERVER")
    if not os.getenv("MAIL_USERNAME"):
        missing.append("MAIL_USERNAME")
    if not os.getenv("MAIL_PASSWORD"):
        missing.append("MAIL_PASSWORD")
    if not os.getenv("MAIL_DEFAULT_SENDER"):
        missing.append("MAIL_DEFAULT_SENDER")
    return missing


def mail_status() -> tuple:
    """
    Whether email delivery is usable, for startup/health checks.

    Returns (configured: bool, missing: list[str]) — `missing` contains only
    environment variable NAMES, never values.
    """
    provider, _api_key, _from_email, missing = _resolve_provider()
    return provider is not None, missing


def _resolve_provider() -> tuple:
    """
    Decide which email transport to use.

    Returns (provider, api_key, from_email, missing) where provider is one of
    "resend" | "brevo" | "sendgrid" | "smtp" | None and `missing` holds the
    NAMES of missing variables (for safe diagnostics; values are never logged).

    Selection:
      - EMAIL_PROVIDER forces a transport ("resend"|"brevo"|"sendgrid"|"smtp").
      - Otherwise (auto): HTTP API providers are tried first because they work
        even where outbound SMTP is blocked, then classic SMTP.
    """
    provider = (os.getenv("EMAIL_PROVIDER", "") or "").strip().lower()
    default_sender = (os.getenv("MAIL_DEFAULT_SENDER", "") or "").strip()

    if provider in _API_PROVIDERS:
        key_var = _API_KEY_VAR[provider]
        api_key = (os.getenv(key_var, "") or "").strip()
        from_email = default_sender
        if provider == "resend" and not from_email:
            from_email = (os.getenv("RESEND_FROM", "") or "").strip()
        missing = []
        if not api_key:
            missing.append(key_var)
        if not from_email:
            missing.append("RESEND_FROM" if provider == "resend" else "MAIL_DEFAULT_SENDER")
        if missing:
            return None, None, None, missing
        return provider, api_key, from_email, []

    if provider == "smtp":
        missing = _missing_mail_vars()
        if missing:
            return None, None, None, missing
        return "smtp", None, None, []

    # Auto: port-443 HTTP APIs first, then SMTP.
    resend_key = (os.getenv("RESEND_API_KEY", "") or "").strip()
    if resend_key:
        from_email = default_sender or (os.getenv("RESEND_FROM", "") or "").strip()
        if from_email:
            return "resend", resend_key, from_email, []
    brevo_key = (os.getenv("BREVO_API_KEY", "") or "").strip()
    if brevo_key and default_sender:
        return "brevo", brevo_key, default_sender, []
    sendgrid_key = (os.getenv("SENDGRID_API_KEY", "") or "").strip()
    if sendgrid_key and default_sender:
        return "sendgrid", sendgrid_key, default_sender, []

    missing = _missing_mail_vars()
    if missing:
        return None, None, None, missing
    return "smtp", None, None, []


def _smtp_connect(mail_server: str, mail_port: int):
    """
    Connect to the SMTP server and upgrade to TLS.

    - Port 465: implicit SSL/TLS (SMTP_SSL) — Gmail's recommended port.
    - Any other port (typically 587): plaintext connect, then STARTTLS.
    """
    if mail_port == 465:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(mail_server, mail_port, context=context, timeout=15)
        server.ehlo()
        return server

    server = smtplib.SMTP(mail_server, mail_port, timeout=15)
    server.ehlo()
    if mail_port != 25:
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
    return server


def _send_via_smtp(to_email: str, subject: str, body_text: str, body_html: str) -> tuple:
    """Send over classic SMTP. Returns (sent, reason)."""
    mail_server = (os.getenv("MAIL_SERVER", "") or "").strip()
    try:
        mail_port = int((os.getenv("MAIL_PORT", "") or "587").strip())
    except (TypeError, ValueError):
        print("[MAIL] Email send failed: invalid MAIL_PORT (must be an integer)")
        return False, "config_missing"
    mail_username = (os.getenv("MAIL_USERNAME", "") or "").strip()
    mail_password = (os.getenv("MAIL_PASSWORD", "") or "").strip()
    mail_default_sender = (os.getenv("MAIL_DEFAULT_SENDER", "") or "").strip() or mail_username

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_default_sender
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    server = None
    try:
        server = _smtp_connect(mail_server, mail_port)
        print(f"[MAIL] SMTP connection successful (server={mail_server}, port={mail_port}, tls=yes)")
        server.login(mail_username, mail_password)
        server.sendmail(mail_default_sender, [to_email], msg.as_string())
        return True, ""
    except Exception as e:
        # Log the exception TYPE plus a sanitized message — never credentials.
        print(f"[MAIL] Email send failed: {_sanitize_exception(e)}")
        return False, "smtp_error"
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                pass


def _send_via_api(provider: str, api_key: str, from_email: str, to_email: str,
                  subject: str, body_text: str, body_html: str) -> tuple:
    """
    Send via an HTTP email API over port 443 — works on hosts (like Render)
    where outbound SMTP is blocked. Returns (sent, reason).

    Logging is limited to provider name, port, and HTTP status: never the API
    key, request headers, request body, or OTP values.
    """
    if provider == "resend":
        url = "https://api.resend.com/emails"
        headers = {"Authorization": f"Bearer {api_key}",
                   "Content-Type": "application/json"}
        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": body_text,
            "html": body_html,
        }
    elif provider == "brevo":
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {"api-key": api_key,
                   "Content-Type": "application/json",
                   "accept": "application/json"}
        payload = {
            "sender": {"email": from_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body_text,
            "htmlContent": body_html,
        }
    else:  # sendgrid
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {"Authorization": f"Bearer {api_key}",
                   "Content-Type": "application/json"}
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": body_text},
                {"type": "text/html", "value": body_html},
            ],
        }

    try:
        resp = http_requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"[MAIL] {provider} API send failed: {_sanitize_exception(e)}")
        return False, "api_error"

    if resp.status_code not in (200, 201, 202):
        # Status only — response bodies can echo addresses; keys are in headers.
        print(f"[MAIL] {provider} API send failed: HTTP {resp.status_code}")
        return False, "api_error"

    print(f"[MAIL] {provider} API send successful (port 443)")
    return True, ""


def _build_email(otp_code: str, purpose: str) -> tuple:
    """Build (subject, body_text, body_html) for the OTP email."""
    if purpose == "password_reset":
        subject = "VaultX Bank — Password Reset Code"
        heading = "Password Reset Request"
        body_text = (
            f"You requested a password reset for your VaultX Bank account.\n\n"
            f"Your verification code is:\n\n"
            f"    {otp_code}\n\n"
            f"This code expires in 10 minutes.\n\n"
            f"If you did not request this, please ignore this email."
        )
        body_html = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
            <div style="background: #1e2d47; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <h1 style="color: white; margin: 0; font-size: 20px;">VaultX Bank</h1>
            </div>
            <h2 style="color: #1e293b; font-size: 18px; margin-bottom: 16px;">{heading}</h2>
            <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                You requested a password reset for your VaultX Bank account.
            </p>
            <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">Your verification code</p>
                <p style="color: #1e2d47; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 0; font-family: monospace;">{otp_code}</p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                This code expires in 10 minutes. If you did not request this, please ignore this email.
            </p>
        </div>
        """
    else:
        subject = "VaultX Bank — Email Verification Code"
        heading = "Email Verification"
        body_text = (
            f"Your VaultX Bank verification code is:\n\n"
            f"    {otp_code}\n\n"
            f"This code expires in 10 minutes."
        )
        body_html = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
            <div style="background: #1e2d47; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <h1 style="color: white; margin: 0; font-size: 20px;">VaultX Bank</h1>
            </div>
            <h2 style="color: #1e293b; font-size: 18px; margin-bottom: 16px;">{heading}</h2>
            <p style="color: #475569; font-size: 14px; line-height: 1.6;">
                Your VaultX Bank verification code is below.
            </p>
            <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">Your verification code</p>
                <p style="color: #1e2d47; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 0; font-family: monospace;">{otp_code}</p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                This code expires in 10 minutes.
            </p>
        </div>
        """
    return subject, body_text, body_html


def send_otp_email(to_email: str, otp_code: str, purpose: str = "password_reset") -> tuple:
    """
    Send an OTP email to the user.

    Returns (sent: bool, reason: str). `reason` is "" on success, otherwise a
    machine-readable code for callers:
      - "config_missing"    required mail variables are not set
      - "smtp_error"        SMTP connection/login/send failed
      - "api_error"         HTTP email API call failed
    This function NEVER logs credentials, passwords, API keys, or OTP values.
    """
    print("[MAIL] Attempting to send password reset email" if purpose == "password_reset"
          else "[MAIL] Attempting to send verification email")

    subject, body_text, body_html = _build_email(otp_code, purpose)

    provider, api_key, from_email, missing = _resolve_provider()
    if provider is None:
        # Log only variable NAMES, never values.
        print(f"[MAIL] Email not configured. Missing required variables: {', '.join(missing)}")
        return False, "config_missing"

    if provider in _API_PROVIDERS:
        sent, reason = _send_via_api(provider, api_key, from_email, to_email,
                                     subject, body_text, body_html)
    else:
        sent, reason = _send_via_smtp(to_email, subject, body_text, body_html)

    if sent:
        print("[MAIL] Password reset email sent successfully" if purpose == "password_reset"
              else "[MAIL] Verification email sent successfully")
    return sent, reason
