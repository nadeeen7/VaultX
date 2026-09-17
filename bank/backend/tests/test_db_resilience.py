"""
Database resilience tests for Render PostgreSQL idle-drop failures.

Covers the production incident:
    psycopg2.OperationalError: consuming input failed:
    SSL error: unexpected eof while reading
raised while reading the users table during POST /api/auth/forgot-password.

Everything runs against the throwaway SQLite file from conftest — the
production PostgreSQL database is never touched. All simulations are
surgical monkeypatches with try/finally restore; tests self-clean so the
rest of the suite is never affected.
"""
import logging
import sqlite3

from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

from conftest import make_user
from app.models import db, User, OTP


# The EXACT production failure, reproduced against sqlite's DBAPI where the
# real psycopg2 message text is carried through SQLAlchemy unchanged.
PROD_SSL_EOF = "consuming input failed: SSL error: unexpected eof while reading"


def _prod_shaped_error():
    """Build an OperationalError shaped exactly like the production one."""
    return OperationalError(
        "SELECT 1", {}, sqlite3.OperationalError(PROD_SSL_EOF)
    )


def _install_boom_query(monkeypatch):
    """Make every User lookup fail exactly like the incident: the session
    opens a real transaction (the SELECT starts) and then the connection dies
    mid-read with the production SSL EOF error.

    Patched at the _QueryProperty.__get__ level because User.query is read off
    the MODEL CLASS and monkeypatch.setattr would read the descriptor's value
    to save it — which itself requires an app context.
    """
    import flask_sqlalchemy.model as fsa_model

    class BoomQuery:
        def filter_by(self, *a, **k):
            db.session.execute(text("SELECT 1"))  # begin a real transaction
            raise _prod_shaped_error()            # ...then the connection dies

    original_get = fsa_model._QueryProperty.__get__

    def boom_get(self, obj, cls):
        if cls is User:
            return BoomQuery()
        return original_get(self, obj, cls)

    monkeypatch.setattr(fsa_model._QueryProperty, "__get__", boom_get)


# ════════════════════════════════════════════════════════════════════════
# SECTION 1: ENGINE CONFIGURATION (what ships to Render)
# ════════════════════════════════════════════════════════════════════════

class TestEngineConfiguration:
    def test_production_pool_options(self, app):
        """Production engine must be configured with defensive pool settings."""
        opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert opts["pool_pre_ping"] is True
        assert 60 <= opts["pool_recycle"] <= 900   # 280s by default
        assert opts["pool_timeout"] >= 5           # fail fast, never hang
        assert opts["pool_size"] >= 1
        assert opts["max_overflow"] >= 0

    def test_live_engine_uses_pre_ping_and_recycle(self, app):
        """The created engine itself carries the defensive pool settings."""
        with app.app_context():
            engine = db.engine
            assert engine.pool._pre_ping is True
            assert engine.pool._recycle == app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_recycle"]

    def test_ssl_mode_preserved_when_present(self):
        """An sslmode already in DATABASE_URL must be preserved untouched."""
        from config.config import _require_ssl_if_missing
        url = "postgresql://u@h:5432/db?sslmode=verify-full&application_name=vaultx"
        assert _require_ssl_if_missing(url) is url  # unchanged, same object

    def test_ssl_mode_added_only_when_missing(self):
        """Missing sslmode is appended; existing query params are kept."""
        from config.config import _require_ssl_if_missing
        out = _require_ssl_if_missing("postgresql://u@h:5432/db?connect_timeout=5")
        assert out.count("sslmode=") == 1
        assert "sslmode=require" in out
        assert "connect_timeout=5" in out

    def test_ssl_mode_added_to_paramless_url(self):
        from config.config import _require_ssl_if_missing
        out = _require_ssl_if_missing("postgresql://u@h:5432/db")
        assert out == "postgresql://u@h:5432/db?sslmode=require"


# ════════════════════════════════════════════════════════════════════════
# SECTION 2: STALE CONNECTION RECOVERY VIA pool_pre_ping
# ════════════════════════════════════════════════════════════════════════

class TestStaleConnectionRecovery:
    def test_stale_connection_discarded_and_replaced(self, app):
        """A connection whose socket dies while idle in the pool is transparently
        replaced on next checkout — the exact Render idle-drop scenario."""
        with app.app_context():
            engine = db.engine

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # healthy connection -> pooled

            # Kill the raw DBAPI connection BEHIND the pool's back while it
            # sits checked-in — what the Render LB does to idle TCP streams.
            pooled = list(engine.pool._pool.queue)
            assert pooled, "expected a pooled connection to stale-ify"
            pooled[0].dbapi_connection.close()

            # The next checkout must succeed WITHOUT raising: pre_ping detects
            # the dead socket, discards it, and opens a fresh connection.
            with engine.connect() as conn:
                assert conn.execute(text("SELECT 1")).scalar() == 1

    def test_ping_failure_with_disconnect_classification_recovers(self, app):
        """During pre-ping, a disconnect-classified DBAPI failure (the psycopg2
        'SSL error: unexpected eof' family) is swallowed and the connection
        replaced — the request itself never sees an error."""
        with app.app_context():
            engine = db.engine
            calls = {"ping": 0}

            real_ping = engine.dialect.do_ping
            real_is_disconnect = engine.dialect.is_disconnect

            def flaky_ping(conn):
                calls["ping"] += 1
                raise sqlite3.OperationalError(PROD_SSL_EOF)

            def classify_as_disconnect(e, conn, cursor):
                return True  # what PGDialect_psycopg2 does for this message

            engine.dialect.do_ping = flaky_ping
            engine.dialect.is_disconnect = classify_as_disconnect
            try:
                with engine.connect() as conn:
                    assert conn.execute(text("SELECT 1")).scalar() == 1
                assert calls["ping"] >= 1
            finally:
                engine.dialect.do_ping = real_ping
                engine.dialect.is_disconnect = real_is_disconnect

            # Engine stays healthy afterwards
            with engine.connect() as conn:
                assert conn.execute(text("SELECT 1")).scalar() == 1

    def test_orm_queries_work_after_stale_pooled_connection(self, app, db_session):
        """ORM traffic (User.query — the exact query in the incident) works
        after a pooled connection went stale."""
        make_user(db_session, "staleuser", "staleuser@example.com")

        with app.app_context():
            engine = db.engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            pooled = list(engine.pool._pool.queue)
            if pooled:
                pooled[0].dbapi_connection.close()

        # Fresh request-context ORM query on the same engine
        assert User.query.filter_by(email="staleuser@example.com").first() is not None

    def test_pooled_connection_reused_when_healthy(self, app):
        """Healthy connections are reused (pool actually pools; pre_ping only
        adds a cheap ping, not a reconnect)."""
        with app.app_context():
            engine = db.engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            assert engine.pool.checkedin() >= 1

    def test_connection_returned_to_pool_after_request(self, app, client):
        """After a request finishes, its DB session is removed and the
        connection is checked back into the pool (no per-request leaks)."""
        with app.app_context():
            pool = db.engine.pool  # hold the object; no context needed to read counters

        # Request that touches the DB (fails auth but performs user lookup)
        resp = client.post("/api/auth/login",
                           json={"email": "nobody@x.test", "password": "Whatever1"})
        assert resp.status_code == 401

        # Nothing is left checked out: the request's connection was returned
        assert pool.checkedout() == 0, "no connection may stay checked out after the request"
        assert pool.checkedin() >= 1, "a pooled connection is available again"


# ════════════════════════════════════════════════════════════════════════
# SECTION 3: OPERATIONALERROR HANDLING — ROLLBACK + SAFE RESPONSE
# ════════════════════════════════════════════════════════════════════════

class TestOperationalErrorHandling:
    def test_operational_error_returns_safe_503_and_rolls_back(self, app, client, monkeypatch):
        """A mid-request DB outage yields a generic 503 (no driver internals),
        the session is rolled back, and the app recovers on the next request."""
        from app.auth import hash_password

        with app.app_context():
            u = User(username="dboutuser", email="dbout@example.com",
                     password_hash=hash_password("Str0ngPass!"), first_name="D", last_name="B",
                     role="user", auth_provider="email")
            db.session.add(u)
            db.session.commit()

        rollback_events = []

        with monkeypatch.context() as m:
            # Force ANY User lookup in the request to fail like the incident
            _install_boom_query(m)

            listener = lambda s: rollback_events.append("rollback")
            event.listen(db.session.session_factory, "after_rollback", listener)
            try:
                resp = client.post("/api/auth/forgot-password",
                                   json={"email": "dbout@example.com"})
            finally:
                event.remove(db.session.session_factory, "after_rollback", listener)

            assert resp.status_code == 503
            body = resp.get_json()
            assert body == {"error": "Service temporarily unavailable. Please try again shortly."}
            # No internals leaked to the client
            assert "SQL" not in str(body) and "psycopg" not in str(body).lower()
            assert rollback_events, "session must be rolled back on OperationalError"

        # The app recovers immediately afterwards
        resp2 = client.post("/api/auth/forgot-password", json={"email": "nobody@x.test"})
        assert resp2.status_code == 200

    def test_operational_error_logging_is_safe(self, app, client, monkeypatch, caplog):
        """Diagnostics must name the failure class but never leak the URL,
        credentials, SQL, parameters, OTPs, or tokens."""
        with monkeypatch.context() as m:
            _install_boom_query(m)
            with caplog.at_level(logging.ERROR, logger="vaultx.db"):
                resp = client.post("/api/auth/forgot-password",
                                   json={"email": "logsafe@example.com"})
            assert resp.status_code == 503

        blob = "\n".join(r.getMessage() for r in caplog.records).lower()
        assert "database connection error" in blob
        assert "exception=operationalerror" in blob
        # Secrets / sensitive material must never appear
        assert "postgres" not in blob          # scheme of any DATABASE_URL
        assert "password" not in blob
        assert "otp" not in blob
        assert "select" not in blob            # no SQL text
        assert caplog.text.strip() != "" and "url" not in blob

    def test_existing_error_handlers_intact(self, client):
        """Centralized error handling unchanged: 404/405 shapes preserved."""
        assert client.get("/api/definitely-not-a-route").status_code == 404
        assert client.get("/api/auth/login").status_code == 405

    def test_session_usable_after_handled_outage(self, app, db_session):
        """After a rollback the scoped session is clean and can commit again."""
        with app.app_context():
            try:
                db.session.execute(text("SELECT * FROM no_such_table_xyz"))
            except Exception:
                db.session.rollback()
            from app.models import SecurityEvent
            ev = SecurityEvent(event_id="dbresilience-probe-1", event_type="LOGIN_SUCCESS",
                               status="SUCCESS", severity="LOW")
            db.session.add(ev)
            db.session.commit()
            assert SecurityEvent.query.filter_by(event_id="dbresilience-probe-1").first() is not None
            # cleanup
            SecurityEvent.query.filter_by(event_id="dbresilience-probe-1").delete()
            db.session.commit()


# ════════════════════════════════════════════════════════════════════════
# SECTION 4: FORGOT-PASSWORD FLOW UNCHANGED
# ════════════════════════════════════════════════════════════════════════

class TestForgotPasswordUnchanged:
    def test_full_flow_with_pool_resilience_active(self, app, client, db_session, monkeypatch):
        """Request OTP -> verify -> reset -> relogin, all with pre_ping+recycle
        engine options active: the flow is byte-for-byte unchanged."""
        from conftest import capture_otp, VALID_PASSWORD

        make_user(db_session, "resiluser", "resiluser@example.com")

        otp_code = capture_otp(client, "resiluser@example.com", monkeypatch)

        resp = client.post("/api/auth/verify-otp",
                           json={"email": "resiluser@example.com", "otp": otp_code})
        assert resp.status_code == 200
        reset_token = resp.get_json()["reset_token"]

        new_password = "FreshPass123"
        resp = client.post("/api/auth/reset-password", json={
            "email": "resiluser@example.com", "reset_token": reset_token,
            "new_password": new_password, "confirm_password": new_password})
        assert resp.status_code == 200

        resp = client.post("/api/auth/login",
                           json={"email": "resiluser@example.com", "password": new_password})
        assert resp.status_code == 200
        assert resp.get_json()["token"]

        # Old password no longer works
        resp = client.post("/api/auth/login",
                           json={"email": "resiluser@example.com",
                                 "password": VALID_PASSWORD})
        assert resp.status_code == 401

    def test_otp_rows_not_duplicated_by_db_errors(self, app, client, db_session, monkeypatch):
        """A DB failure during forgot-password must not leave extra OTP rows:
        the failed transaction was rolled back, nothing partially committed."""
        with app.app_context():
            before = OTP.query.filter_by(email="rollbackotp@example.com").count()

        with monkeypatch.context() as m:
            _install_boom_query(m)
            resp = client.post("/api/auth/forgot-password",
                               json={"email": "rollbackotp@example.com"})
            assert resp.status_code == 503

        with app.app_context():
            after = OTP.query.filter_by(email="rollbackotp@example.com").count()
        assert before == after == 0

    def test_non_db_errors_still_reach_their_own_handlers(self, client):
        """Only OperationalError is remapped: validation errors still 400."""
        resp = client.post("/api/auth/forgot-password", json={})
        assert resp.status_code == 400
        resp = client.post("/api/auth/forgot-password",
                           json={"email": "not-an-email"})
        assert resp.status_code == 400
