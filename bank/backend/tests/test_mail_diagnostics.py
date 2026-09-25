"""Transport diagnostics use synthetic data and never send real email."""
import json
from types import SimpleNamespace
import pytest
from conftest import make_user
from app.routes import auth as auth_routes
from app.services import email_service


def configure_resend(monkeypatch):
    monkeypatch.setenv('EMAIL_PROVIDER', 'resend')
    monkeypatch.setenv('RESEND_API_KEY', 'synthetic-resend-key')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', 'sender@example.test')
    monkeypatch.setenv('BREVO_API_KEY', 'synthetic-stale-brevo-key')


def records(capsys):
    return [json.loads(line[7:]) for line in capsys.readouterr().out.splitlines()
            if line.startswith('[MAIL] {')]


def test_actual_provider_logged_even_with_unused_resend_key(monkeypatch, capsys):
    configure_resend(monkeypatch)
    monkeypatch.setenv('EMAIL_PROVIDER', 'smtp')
    email_service.log_mail_configuration()
    record = records(capsys)[0]
    assert record['selected_provider'] == 'smtp'
    assert record['configured_provider'] == 'smtp'
    assert record['resend_key_present'] is True


def test_explicit_resend_attempt_and_status_are_logged(monkeypatch, capsys):
    configure_resend(monkeypatch)
    calls = []
    def post(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200)
    monkeypatch.setattr(email_service.http_requests, 'post', post)
    assert email_service.send_otp_email('recipient@example.test', '827193') == (True, '')
    assert calls[0][0] == 'https://api.resend.com/emails'
    assert calls[0][1]['headers']['Authorization'] == 'Bearer synthetic-resend-key'
    assert calls[0][1]['json']['from'] == 'sender@example.test'
    logs = records(capsys)
    assert any(r.get('configured_provider') == 'resend' for r in logs)
    assert any(r.get('http_status') == 200 and r.get('result') == 'accepted' for r in logs)
    output = json.dumps(logs)
    for sensitive in ('827193', 'synthetic-resend-key', 'recipient@example.test', 'sender@example.test'):
        assert sensitive not in output


@pytest.mark.parametrize('transport', ['api', 'smtp'])
def test_exception_messages_never_logged(monkeypatch, capsys, transport):
    configure_resend(monkeypatch)
    sensitive = 'OTP 827193 recipient@example.test password tiny key xyz token abc email contents'
    def fail(*args, **kwargs):
        raise RuntimeError(sensitive)
    if transport == 'api':
        monkeypatch.setattr(email_service.http_requests, 'post', fail)
    else:
        monkeypatch.setenv('EMAIL_PROVIDER', 'smtp')
        monkeypatch.setattr(email_service, '_smtp_connect', fail)
    assert email_service.send_otp_email('recipient@example.test', '827193')[0] is False
    out = capsys.readouterr().out
    assert 'RuntimeError' in out
    for value in ('827193', 'recipient@example.test', 'tiny', 'xyz', 'abc', 'email contents'):
        assert value not in out


def test_unknown_and_google_only_requests_skip_transport(client, db_session, monkeypatch, capsys):
    make_user(db_session, 'diaggoogle', 'diaggoogle@example.test', google=True)
    def unexpected(*args, **kwargs):
        pytest.fail('Ineligible reset reached email transport')
    monkeypatch.setattr(auth_routes, 'send_otp_email', unexpected)
    responses = [client.post('/api/auth/forgot-password', json={'email': address})
                 for address in ('diagmissing@example.test', 'diaggoogle@example.test')]
    assert all(r.status_code == 200 for r in responses)
    assert responses[0].json == responses[1].json
    logs = records(capsys)
    assert sum(r.get('result') == 'not_dispatched' for r in logs) == 2
    assert all('trace_id' in r for r in logs)
    assert 'diagmissing' not in json.dumps(logs) and 'diaggoogle' not in json.dumps(logs)


def test_failure_and_cooldown_keep_generic_response(client, db_session, monkeypatch):
    make_user(db_session, 'diagfailure', 'diagfailure@example.test')
    make_user(db_session, 'diagcooldown', 'diagcooldown@example.test')
    generic = client.post('/api/auth/forgot-password', json={'email': 'diagabsent@example.test'})
    monkeypatch.setattr(auth_routes, 'send_otp_email', lambda *a, **k: (False, 'api_error'))
    failed = client.post('/api/auth/forgot-password', json={'email': 'diagfailure@example.test'})
    monkeypatch.setattr(auth_routes, 'send_otp_email', lambda *a, **k: (True, ''))
    accepted = client.post('/api/auth/forgot-password', json={'email': 'diagcooldown@example.test'})
    def unexpected(*args, **kwargs):
        pytest.fail('Cooldown failed to suppress a second send')
    monkeypatch.setattr(auth_routes, 'send_otp_email', unexpected)
    cooldown = client.post('/api/auth/forgot-password', json={'email': 'diagcooldown@example.test'})
    assert all(r.status_code == 200 and r.json == generic.json for r in (failed, accepted, cooldown))
