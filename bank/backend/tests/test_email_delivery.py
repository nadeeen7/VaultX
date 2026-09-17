"""
Email delivery transport tests.

The forgot-password OTP email must be deliverable from hosts where outbound
SMTP is blocked (Render: "OSError: [Errno 101] Network is unreachable").
These tests cover the port-443 HTTP API transports (Resend/Brevo/SendGrid),
provider selection, failure reason codes, secret-free logging, and the full
forgot-password flow using a mocked HTTP API.

No real emails are sent and no real API keys are used.
"""
import pytest

from conftest import make_user
from app.models import db, OTP
from app.services import email_service


# ════════════════════════════════════════════════════════════════════════
# Provider selection
# ════════════════════════════════════════════════════════════════════════

class TestProviderSelection:
    def test_api_provider_autodetected_from_key(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "VaultX <test@vaultx.test>")
        provider, api_key, from_email, missing = email_service._resolve_provider()
        assert provider == "resend"
        assert api_key == "re_test_key_not_real"
        assert "test@vaultx.test" in from_email
        assert missing == []

    def test_smtp_still_selected_when_no_api_keys(self, monkeypatch):
        for var in ("RESEND_API_KEY", "BREVO_API_KEY", "SENDGRID_API_KEY", "EMAIL_PROVIDER"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("MAIL_SERVER", "smtp.test.local")
        monkeypatch.setenv("MAIL_USERNAME", "test@vaultx.test")
        monkeypatch.setenv("MAIL_PASSWORD", "test-password-not-real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "test@vaultx.test")
        provider, _, _, missing = email_service._resolve_provider()
        assert provider == "smtp"
        assert missing == []

    def test_no_transport_reports_missing_variable_names_only(self, monkeypatch):
        for var in ("RESEND_API_KEY", "BREVO_API_KEY", "SENDGRID_API_KEY",
                    "EMAIL_PROVIDER", "MAIL_SERVER", "MAIL_USERNAME",
                    "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER"):
            monkeypatch.delenv(var, raising=False)
        provider, _, _, missing = email_service._resolve_provider()
        assert provider is None
        assert set(missing) == {"MAIL_SERVER", "MAIL_USERNAME", "MAIL_PASSWORD",
                                "MAIL_DEFAULT_SENDER"}

    def test_forced_provider_with_missing_key_names_the_variable(self, monkeypatch):
        monkeypatch.setenv("EMAIL_PROVIDER", "brevo")
        monkeypatch.delenv("BREVO_API_KEY", raising=False)
        provider, _, _, missing = email_service._resolve_provider()
        assert provider is None
        assert "BREVO_API_KEY" in missing

    def test_mail_status_usable_flag(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "VaultX <test@vaultx.test>")
        ok, missing = email_service.mail_status()
        assert ok is True and missing == []


# ════════════════════════════════════════════════════════════════════════
# HTTP API transports
# ════════════════════════════════════════════════════════════════════════

class TestApiTransports:
    def _resend_env(self, monkeypatch):
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "VaultX <test@vaultx.test>")
        monkeypatch.delenv("EMAIL_PROVIDER", raising=False)

    def test_resend_success_sends_wellformed_payload(self, monkeypatch, capsys):
        self._resend_env(monkeypatch)

        captured = {}

        class FakeResp:
            status_code = 200

        def fake_post(url, json=None, headers=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResp()

        monkeypatch.setattr(email_service.http_requests, "post", fake_post)
        sent, reason = email_service.send_otp_email("user@example.com", "123456")
        assert sent is True and reason == ""
        assert captured["url"] == "https://api.resend.com/emails"
        assert captured["json"]["to"] == ["user@example.com"]
        assert "123456" in captured["json"]["text"]      # OTP inside the mail body
        assert "123456" in captured["json"]["html"]
        assert captured["headers"]["Authorization"] == "Bearer re_test_key_not_real"
        # Logs never contain the API key or the OTP value
        out = capsys.readouterr().out
        assert "re_test_key_not_real" not in out
        assert "123456" not in out

    def test_brevo_success(self, monkeypatch):
        monkeypatch.setenv("EMAIL_PROVIDER", "brevo")
        monkeypatch.setenv("BREVO_API_KEY", "xkeysib_test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "test@vaultx.test")

        captured = {}

        class FakeResp:
            status_code = 201

        def fake_post(url, json=None, headers=None, timeout=None):
            captured.update(url=url, json=json)
            return FakeResp()

        monkeypatch.setattr(email_service.http_requests, "post", fake_post)
        sent, reason = email_service.send_otp_email("user@example.com", "654321")
        assert sent is True and reason == ""
        assert captured["url"].startswith("https://api.brevo.com/")
        assert captured["json"]["to"] == [{"email": "user@example.com"}]

    def test_sendgrid_success(self, monkeypatch):
        monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
        monkeypatch.setenv("SENDGRID_API_KEY", "SG.test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "test@vaultx.test")

        captured = {}

        class FakeResp:
            status_code = 202

        def fake_post(url, json=None, headers=None, timeout=None):
            captured.update(url=url, json=json)
            return FakeResp()

        monkeypatch.setattr(email_service.http_requests, "post", fake_post)
        sent, reason = email_service.send_otp_email("user@example.com", "111222")
        assert sent is True and reason == ""
        assert captured["url"] == "https://api.sendgrid.com/v3/mail/send"
        assert captured["json"]["personalizations"][0]["to"] == [{"email": "user@example.com"}]

    def test_api_http_error_returns_api_error_reason(self, monkeypatch):
        self._resend_env(monkeypatch)

        class FakeResp:
            status_code = 422

        monkeypatch.setattr(email_service.http_requests, "post",
                            lambda *a, **k: FakeResp())
        sent, reason = email_service.send_otp_email("user@example.com", "123456")
        assert sent is False and reason == "api_error"

    def test_api_network_exception_returns_api_error_reason(self, monkeypatch):
        self._resend_env(monkeypatch)

        def boom(*a, **k):
            raise ConnectionError("[Errno 101] Network is unreachable")

        monkeypatch.setattr(email_service.http_requests, "post", boom)
        sent, reason = email_service.send_otp_email("user@example.com", "123456")
        assert sent is False and reason == "api_error"


# ════════════════════════════════════════════════════════════════════════
# SMTP path unchanged
# ════════════════════════════════════════════════════════════════════════

class TestSmtpPath:
    def test_smtp_failure_reason_unchanged(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.delenv("BREVO_API_KEY", raising=False)
        monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
        monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
        monkeypatch.setenv("MAIL_SERVER", "smtp.test.local")
        monkeypatch.setenv("MAIL_PORT", "587")
        monkeypatch.setenv("MAIL_USERNAME", "test@vaultx.test")
        monkeypatch.setenv("MAIL_PASSWORD", "test-password-not-real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "test@vaultx.test")

        class Boom:
            def __init__(self, *a, **k):
                raise OSError("[Errno 101] Network is unreachable")

        monkeypatch.setattr(email_service.smtplib, "SMTP", Boom)
        sent, reason = email_service.send_otp_email("user@example.com", "123456")
        assert sent is False and reason == "smtp_error"


# ════════════════════════════════════════════════════════════════════════
# Forgot-password flow over the HTTP API transport (end-to-end)
# ════════════════════════════════════════════════════════════════════════

class TestForgotPasswordViaApi:
    def test_forgot_password_full_flow_via_http_api(self, app, client, db_session, monkeypatch):
        """OTP request -> verify -> reset -> relogin, with email sent through
        the port-443 API path (the Render-viable transport)."""
        make_user(db_session, "apimailuser", "apimailuser@example.com")

        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_not_real")
        monkeypatch.setenv("MAIL_DEFAULT_SENDER", "VaultX <test@vaultx.test>")
        for var in ("EMAIL_PROVIDER", "BREVO_API_KEY", "SENDGRID_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        captured = {}

        class FakeResp:
            status_code = 200

        def fake_post(url, json=None, headers=None, timeout=None):
            captured["json"] = json
            return FakeResp()

        # Patch the requests module as imported by the REAL email service
        import app.routes.auth as auth_routes
        monkeypatch.setattr(email_service.http_requests, "post", fake_post)
        monkeypatch.setattr(auth_routes, "send_otp_email", email_service.send_otp_email)

        resp = client.post("/api/auth/forgot-password",
                           json={"email": "apimailuser@example.com"})
        assert resp.status_code == 200
        assert "verification code has been sent" in resp.get_json()["message"].lower()

        # The email "went out" through Resend with the OTP in the body
        assert captured["json"]["to"] == ["apimailuser@example.com"]
        body = captured["json"]["text"]
        otp_code = next(w for w in body.split() if w.isdigit() and len(w) == 6)

        # delivered_at set only after a successful send (rate-limit semantics preserved)
        rec = OTP.query.filter_by(email="apimailuser@example.com",
                                  purpose="password_reset").order_by(
            OTP.created_at.desc()).first()
        assert rec is not None and rec.delivered_at is not None

        # Continue the flow with the delivered code
        resp = client.post("/api/auth/verify-otp",
                           json={"email": "apimailuser@example.com", "otp": otp_code})
        assert resp.status_code == 200
        reset_token = resp.get_json()["reset_token"]

        resp = client.post("/api/auth/reset-password", json={
            "email": "apimailuser@example.com", "reset_token": reset_token,
            "new_password": "ApiResetPass1", "confirm_password": "ApiResetPass1"})
        assert resp.status_code == 200

        resp = client.post("/api/auth/login",
                           json={"email": "apimailuser@example.com",
                                 "password": "ApiResetPass1"})
        assert resp.status_code == 200
        assert resp.get_json()["token"]
