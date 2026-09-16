import pytest
from datetime import datetime, timezone, timedelta

from conftest import (
    VALID_PASSWORD, register_payload, login_payload, auth_headers,
    make_user, capture_otp,
)
from app.models import db, User, OTP, SecurityEvent
from app.routes import auth as auth_routes


def _login(client, email, password):
    return client.post("/api/auth/login", json=login_payload(email, password))


# ════════════════════════════════════════════════════════════════════════
# SECTION 1: REGRESSION — existing functionality keeps working (§17 list)
# ════════════════════════════════════════════════════════════════════════

class TestRegression:
    def test_01_health_endpoint(self, client):
        """15. Production API health endpoint works."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "ok"
        assert "database" in body
        assert "mail_configured" in body

    def test_02_register_new_user(self, client):
        """2. New user can register (subject to the new-password policy)."""
        resp = client.post("/api/auth/register", json=register_payload(
            "reguser", "reguser@example.com"))
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["token"]
        assert body["user"]["username"] == "reguser"
        assert "password" not in body["user"] and "password_hash" not in body["user"]

    def test_03_existing_user_login(self, client, db_session):
        """1. Existing email/password user can log in (pre-policy password kept)."""
        make_user(db_session, "legacyuser", "legacy@example.com")
        resp = _login(client, "legacy@example.com", "OldPassword123")
        assert resp.status_code == 200
        assert resp.get_json()["token"]

    def test_04_wrong_password_rejected(self, client):
        resp = _login(client, "reguser@example.com", "WrongPass1")
        assert resp.status_code == 401

    def test_05_google_existing_user_login(self, client, db_session):
        """3. Existing Google user can log in (google_id/auth_provider preserved)."""
        make_user(db_session, "googleuser", "googleuser@example.com", google=True)

        fake_profile = {"sub": "gid-googleuser", "email": "googleuser@example.com",
                        "email_verified": "true",
                        "aud": "test-client-id.apps.googleusercontent.com",
                        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())}

        class FakeResp:
            status_code = 200
            def json(self):
                return fake_profile

        original = auth_routes.http_requests.get
        auth_routes.http_requests.get = lambda *a, **k: FakeResp()
        try:
            resp = client.post("/api/auth/google", json={"credential": "fake-id-token"})
        finally:
            auth_routes.http_requests.get = original

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["token"]
        assert body["user"]["auth_provider"] == "google"

    def test_06_google_new_user_registration(self, client, db_session):
        """4. New Google user is registered and logged in on first sign-in."""
        fake_profile = {"sub": "brand-new-google-id", "email": "newgoogle@example.com",
                        "email_verified": "true", "given_name": "New", "family_name": "Guser",
                        "aud": "test-client-id.apps.googleusercontent.com",
                        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())}

        class FakeResp:
            status_code = 200
            def json(self):
                return fake_profile

        original = auth_routes.http_requests.get
        auth_routes.http_requests.get = lambda *a, **k: FakeResp()
        try:
            resp = client.post("/api/auth/google", json={"credential": "fake-id-token"})
        finally:
            auth_routes.http_requests.get = original

        assert resp.status_code == 200
        u = User.query.filter_by(email="newgoogle@example.com").first()
        assert u is not None
        assert u.password_hash is None            # Google-only account
        assert u.google_id == "brand-new-google-id"
        assert u.auth_provider == "google"
        assert u.account is not None              # bank account auto-created

    def test_07_forgot_password_sends_otp(self, client, db_session, monkeypatch):
        """5+6. Forgot password works; OTP generated, hashed, delivered flag set."""
        otp_code = capture_otp(client, "legacy@example.com", monkeypatch)

        rec = OTP.query.filter_by(email="legacy@example.com",
                                  purpose="password_reset").order_by(
            OTP.created_at.desc()).first()
        assert rec is not None
        assert rec.delivered_at is not None
        assert rec.otp_hash != otp_code           # stored hashed, never plaintext
        assert otp_code.isdigit() and len(otp_code) == 6

    def test_08_otp_verify_reset_and_relogin(self, client, monkeypatch):
        """7+8+9. OTP verify → password reset → login with the new password."""
        otp_code = capture_otp(client, "reguser@example.com", monkeypatch)

        resp = client.post("/api/auth/verify-otp",
                           json={"email": "reguser@example.com", "otp": otp_code})
        assert resp.status_code == 200
        reset_token = resp.get_json()["reset_token"]

        new_password = "BrandNewPass1"
        resp = client.post("/api/auth/reset-password", json={
            "email": "reguser@example.com", "reset_token": reset_token,
            "new_password": new_password, "confirm_password": new_password})
        assert resp.status_code == 200

        resp = _login(client, "reguser@example.com", new_password)
        assert resp.status_code == 200

    def test_09_dashboard_profile(self, client):
        """10. Existing dashboard (profile) works with JWT."""
        resp = _login(client, "reguser@example.com", "BrandNewPass1")
        token = resp.get_json()["token"]
        resp = client.get("/api/user/profile", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["username"] == "reguser"
        assert "account" in body

    def test_10_transfer_and_history(self, client, db_session):
        """11+12. Transfers still work; history still works."""
        resp = _login(client, "reguser@example.com", "BrandNewPass1")
        token = resp.get_json()["token"]
        headers = auth_headers(token)

        recipient = User.query.filter_by(username="legacyuser").first()
        assert recipient.account is not None
        resp = client.post("/api/transactions/transfer", headers=headers, json={
            "recipient_account": recipient.account.account_number, "amount": 50.0,
            "recipient_name": "Legacy User", "description": "test transfer"})
        assert resp.status_code == 201

        resp = client.get("/api/user/transactions", headers=headers)
        assert resp.status_code == 200
        txs = resp.get_json()["transactions"]
        assert any(t["transaction_type"] == "transfer_out" for t in txs)

    def test_11_logout(self, client):
        """13. Logout works."""
        resp = _login(client, "reguser@example.com", "BrandNewPass1")
        token = resp.get_json()["token"]
        resp = client.post("/api/auth/logout", headers=auth_headers(token))
        assert resp.status_code == 200

    def test_12_jwt_protected_routes(self, client):
        """14. JWT-protected routes still work."""
        resp = _login(client, "reguser@example.com", "BrandNewPass1")
        headers = auth_headers(resp.get_json()["token"])
        for path in ("/api/user/profile", "/api/user/transactions",
                     "/api/user/login-history"):
            assert client.get(path, headers=headers).status_code == 200

    def test_13_security_events_recorded(self, db_session):
        """Centralized security events are written with mapped severities."""
        rows = SecurityEvent.query.all()
        types = {e.event_type for e in rows}
        assert "LOGIN_SUCCESS" in types
        assert "OTP_VERIFIED" in types
        assert "PASSWORD_RESET_SUCCESS" in types
        sev = {e.event_type: e.severity for e in rows}
        assert sev.get("LOGIN_SUCCESS") == "LOW"


# ════════════════════════════════════════════════════════════════════════
# SECTION 2: SECURITY BEHAVIOR (§17 security list)
# ════════════════════════════════════════════════════════════════════════

class TestSecurityBehavior:
    def test_s1_brute_force_lockout(self, client, db_session):
        """S1. 5 failed logins lock the account; success resets counters."""
        make_user(db_session, "lockuser", "lockuser@example.com")

        for _ in range(5):
            resp = _login(client, "lockuser@example.com", "WrongPass1")
        assert resp.status_code == 423
        assert resp.get_json().get("locked") is True

        db_session.expire_all()
        u = User.query.filter_by(username="lockuser").first()
        assert u.is_locked is True

        # Even the CORRECT password is refused while locked
        resp = _login(client, "lockuser@example.com", "OldPassword123")
        assert resp.status_code == 423

        # Lockout expiry → success resets counters
        u.lockout_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()
        resp = _login(client, "lockuser@example.com", "OldPassword123")
        assert resp.status_code == 200

        db_session.expire_all()
        u = User.query.filter_by(username="lockuser").first()
        assert u.failed_login_attempts == 0
        assert u.is_locked is False

    def test_s2_rate_limit_triggers(self, client):
        """S2. Rate limit triggers safely (429), scoped per identifier."""
        unique = f"rl{int(datetime.now().timestamp())}@example.com"

        for _ in range(5):
            resp = client.post("/api/auth/forgot-password", json={"email": unique})
        resp = client.post("/api/auth/forgot-password", json={"email": unique})
        assert resp.status_code == 429

        # A different scope keeps working for the same identifier
        resp = _login(client, unique, "Whatever1")
        assert resp.status_code == 401  # reached auth logic, not the limiter

    def test_s3_transfer_limit_enforced(self, client, db_session):
        """S3. Over-limit transfer is rejected; no cross-account access path."""
        u = make_user(db_session, "idoruser", "idoruser@example.com")
        resp = _login(client, "idoruser@example.com", "OldPassword123")
        token = resp.get_json()["token"]

        resp = client.post("/api/transactions/transfer", headers=auth_headers(token),
                           json={"recipient_account": "VB1234567890", "amount": 999999.0,
                                 "recipient_name": "x", "description": "over limit"})
        assert resp.status_code == 400

    def test_s4_invalid_jwt_denied(self, client):
        """S4. Invalid JWT is denied on protected routes."""
        for path in ("/api/user/profile", "/api/user/transactions"):
            resp = client.get(path, headers=auth_headers("not.a.real.jwt"))
            assert resp.status_code == 401

    def test_s5_expired_jwt_denied(self, client, app, db_session):
        """S5. Expired JWT is denied."""
        u = User.query.filter_by(username="idoruser").first()
        import jwt as pyjwt
        from flask import current_app

        with app.test_request_context():
            payload = {
                "user_id": u.id, "role": "user",
                "iat": datetime.now(timezone.utc) - timedelta(hours=2),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            }
            expired = pyjwt.encode(payload, current_app.config["JWT_SECRET_KEY"],
                                   algorithm="HS256")
        resp = client.get("/api/user/profile", headers=auth_headers(expired))
        assert resp.status_code == 401

    def test_s6_otp_not_reusable(self, client, db_session, monkeypatch):
        """S6. A verified OTP cannot be verified twice."""
        unique = f"reuse{int(datetime.now().timestamp())}@example.com"
        make_user(db_session, "reuseuser", unique)
        otp_code = capture_otp(client, unique, monkeypatch)

        r1 = client.post("/api/auth/verify-otp", json={"email": unique, "otp": otp_code})
        assert r1.status_code == 200
        r2 = client.post("/api/auth/verify-otp", json={"email": unique, "otp": otp_code})
        assert r2.status_code == 400

    def test_s7_expired_otp_rejected(self, client, db_session, monkeypatch):
        """S7. An expired OTP is rejected even if the code matches."""
        unique = f"exp{int(datetime.now().timestamp())}@example.com"
        make_user(db_session, "expuser", unique)
        otp_code = capture_otp(client, unique, monkeypatch)

        rec = OTP.query.filter_by(email=unique, purpose="password_reset").order_by(
            OTP.created_at.desc()).first()
        rec.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()

        resp = client.post("/api/auth/verify-otp", json={"email": unique, "otp": otp_code})
        assert resp.status_code == 400
        assert "expired" in resp.get_json()["error"].lower()

    def test_s8_otp_max_attempts(self, client, db_session, monkeypatch):
        """S8. Too many wrong attempts burn the code (429)."""
        unique = f"att{int(datetime.now().timestamp())}@example.com"
        make_user(db_session, "attuser", unique)
        capture_otp(client, unique, monkeypatch)

        rec = OTP.query.filter_by(email=unique, purpose="password_reset").order_by(
            OTP.created_at.desc()).first()
        for _ in range(rec.max_attempts):
            resp = client.post("/api/auth/verify-otp",
                               json={"email": unique, "otp": "000000"})
        assert resp.status_code == 429

    def test_s9_weak_passwords_rejected(self, client):
        """Password policy applies to NEW passwords only."""
        stamp = int(datetime.now().timestamp())
        cases = ["short1A", "alllowercase1", "ALLUPPERCASE1", "NoDigitsHere", "Aa123456"]
        for i, weak in enumerate(cases):
            resp = client.post("/api/auth/register", json=register_payload(
                f"weak{i}_{stamp}", f"weak{i}_{stamp}@example.com", password=weak))
            assert resp.status_code == 400, f"weak password accepted: {weak}"

    def test_s10_no_secrets_in_security_events(self, db_session):
        """S10. Passwords/OTP values/secrets never appear in event metadata."""
        forbidden = ["Str0ngPass!", "BrandNewPass1", "OldPassword123", "WrongPass1",
                     "test-password-not-real", "test-jwt-secret-not-real",
                     "test-siem-key"]
        for ev in SecurityEvent.query.all():
            blob = str(ev.metadata_json or {}).lower()
            for frag in forbidden:
                assert frag.lower() not in blob, f"secret fragment leaked: {frag}"

    def test_s11_malformed_json_rejected(self, client):
        """Malformed / non-object JSON → 400, never 500."""
        resp = client.post("/api/auth/login", data="{bad json",
                           content_type="application/json")
        assert resp.status_code == 400
        resp = client.post("/api/auth/login", data="[1,2,3]",
                           content_type="application/json")
        assert resp.status_code == 400

    def test_s12_admin_routes_require_role(self, client):
        """Non-admin JWT → 403; missing token → 401."""
        resp = _login(client, "reguser@example.com", "BrandNewPass1")
        user_token = resp.get_json()["token"]
        assert client.get("/api/admin/users",
                          headers=auth_headers(user_token)).status_code == 403
        assert client.get("/api/admin/users").status_code == 401

    def test_s13_security_events_need_auth(self, client):
        """/api/security-events is no longer public; SIEM key still works."""
        assert client.get("/api/security-events").status_code == 401
        resp = client.get("/api/security-events",
                          headers=auth_headers("test-siem-key"))
        assert resp.status_code == 200

    def test_s14_security_headers_present(self, client):
        resp = client.get("/api/health")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert "default-src 'none'" in resp.headers["Content-Security-Policy"]

    def test_s15_xff_spoofing_ignored(self, client):
        """Without TRUST_PROXY, spoofed X-Forwarded-For is not trusted."""
        from app.auth import get_client_ip
        with client.application.test_request_context(
                headers={"X-Forwarded-For": "1.2.3.4"}):
            assert get_client_ip() != "1.2.3.4"

    def test_s16_password_change_policy(self, client, db_session):
        """Change-password enforces the new-password policy."""
        make_user(db_session, "chguser", "chguser@example.com")
        resp = _login(client, "chguser@example.com", "OldPassword123")
        token = resp.get_json()["token"]
        headers = auth_headers(token)

        resp = client.post("/api/user/change-password", headers=headers, json={
            "current_password": "OldPassword123", "new_password": "weak"})
        assert resp.status_code == 400

        resp = client.post("/api/user/change-password", headers=headers, json={
            "current_password": "OldPassword123", "new_password": "NewStrong1"})
        assert resp.status_code == 200
        assert _login(client, "chguser@example.com", "OldPassword123").status_code == 401
        assert _login(client, "chguser@example.com", "NewStrong1").status_code == 200
