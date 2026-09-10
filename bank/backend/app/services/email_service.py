import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_otp_email(to_email: str, otp_code: str, purpose: str = "password_reset") -> bool:
    """
    Send an OTP email to the user.
    Returns True if sent successfully, False otherwise.
    """
    mail_server = os.getenv("MAIL_SERVER", "")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME", "")
    mail_password = os.getenv("MAIL_PASSWORD", "")
    mail_default_sender = os.getenv("MAIL_DEFAULT_SENDER", mail_username)

    if not all([mail_server, mail_username, mail_password]):
        print("[WARNING] Email not configured. Set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD.")
        return False

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

    try:
        with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
            server.ehlo()
            if mail_port != 25:
                server.starttls()
                server.ehlo()
            server.login(mail_username, mail_password)
            server.sendmail(mail_default_sender, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send OTP email: {e}")
        return False
