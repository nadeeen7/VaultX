import os
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Redact anything that looks like a credential inside exception text:
# "AUTHENTICATE PLAIN <b64>", "User ... <token>", long base64/hex-ish chunks,
# and anything following "password", "token", or "auth".
_B64_RE = re.compile(r"[A-Za-z0-9+/=_-]{16,}")
_SECRET_WORD_RE = re.compile(
    r"(?i)(password|passwd|token|auth\w*)\s*[:=]?\s*\S+"
)


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
    Return the NAMES of required mail environment variables that are missing.
    Never returns or logs any variable VALUES.
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


def send_otp_email(to_email: str, otp_code: str, purpose: str = "password_reset") -> tuple:
    """
    Send an OTP email to the user.

    Returns (sent: bool, reason: str). `reason` is "" on success, otherwise a
    machine-readable code for callers:
      - "config_missing"    required MAIL_* variables are not set
      - "smtp_error"        connection/login/send failed
    This function NEVER logs credentials, passwords, or OTP values.
    """
    print("[MAIL] Attempting to send password reset email" if purpose == "password_reset"
          else "[MAIL] Attempting to send verification email")

    missing = _missing_mail_vars()
    if missing:
        # Log only variable NAMES, never values.
        print(f"[MAIL] Email not configured. Missing required variables: {', '.join(missing)}")
        return False, "config_missing"

    mail_server = (os.getenv("MAIL_SERVER", "") or "").strip()
    try:
        mail_port = int((os.getenv("MAIL_PORT", "") or "587").strip())
    except (TypeError, ValueError):
        print("[MAIL] Email send failed: invalid MAIL_PORT (must be an integer)")
        return False, "config_missing"
    mail_username = (os.getenv("MAIL_USERNAME", "") or "").strip()
    mail_password = (os.getenv("MAIL_PASSWORD", "") or "").strip()
    mail_default_sender = (os.getenv("MAIL_DEFAULT_SENDER", "") or "").strip() or mail_username

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
            <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">Your verification code</p>
                <p style="color: #1e2d47; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 0; font-family: monospace;">{otp_code}</p>
            </div>
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                This code expires in 10 minutes.
            </p>
        </div>
        """

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
        print(f"[MAIL] Password reset email sent successfully" if purpose == "password_reset"
              else "[MAIL] Verification email sent successfully")
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
