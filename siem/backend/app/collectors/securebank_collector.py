import time
import threading
import requests
from datetime import datetime
from flask import current_app
from app.database import db, socketio
from app.models.security_event import SecurityEvent
from app.models.setting import Setting
from app.models.alert import Alert
from app.detection.rules import detection_engine
from app.detection.correlation_engine import correlation_engine
from app.detection.risk_engine import calculate_transparent_risk_score
from app.ml.anomaly_detector import anomaly_detector
from app.detection.geo_detection import geo_detection_engine
from app.services.ip_service import get_ip_intelligence
from app.services.incident_service import correlate_alert_into_incident
from app.services.alert_dedup import create_or_update_alert
from app.notifications.dispatcher import notification_dispatcher

# Module-level guard to prevent double-start (Flask reloader, multiple create_app calls)
_collector_started = False

class SecureBankCollector:
    """
    Background worker that continuously polls SecureBank's GET /api/security-events API,
    normalizes logs, enforces deduplication, executes detection rules & ML anomaly model,
    and updates Socket.IO real-time clients.
    """

    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None

    def start(self, app):
        global _collector_started
        self.app = app
        if _collector_started:
            print("[SecureBank Collector] Already started, skipping duplicate.")
            return
        _collector_started = True
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[SecureBank Collector] Background collector loop started (once).")

    def stop(self):
        self.running = False

    def _get_checkpoint(self):
        """Retrieve stored synchronization checkpoint from database."""
        try:
            setting = Setting.query.filter_by(key='last_event_timestamp').first()
            if setting and setting.value:
                return setting.value
        except Exception:
            pass
        return "1970-01-01T00:00:00Z"

    def _save_checkpoint(self, last_timestamp):
        """Save latest synchronized event timestamp checkpoint."""
        try:
            setting = Setting.query.filter_by(key='last_event_timestamp').first()
            if not setting:
                setting = Setting(key='last_event_timestamp', value=str(last_timestamp), description="Synchronization checkpoint for SecureBank logs")
                db.session.add(setting)
            else:
                setting.value = str(last_timestamp)
            db.session.commit()
        except Exception as err:
            print(f"[SecureBank Collector] Failed to save checkpoint: {err}")

    @staticmethod
    def _normalize_event_type(raw_type):
        """Normalize event types from SecureBank (UPPER_CASE) to SIEM internal (lowercase_snake)."""
        if not raw_type:
            return 'unknown_activity'
        # SecureBank uses UPPER_CASE like LOGIN_FAILED, TRANSFER_CREATED
        # Map to SIEM's lowercase_snake format used by detection rules
        type_map = {
            'LOGIN_SUCCESS': 'login_success',
            'LOGIN_FAILED': 'login_failed',
            'LOGOUT': 'logout',
            'ACCOUNT_CREATED': 'account_created',
            'ACCOUNT_LOCKED': 'account_locked',
            'TRANSFER_CREATED': 'fund_transfer',
            'TRANSFER_FAILED': 'transfer_failed',
            'PASSWORD_CHANGE': 'password_change',
            'PASSWORD_CHANGE_FAILED': 'password_change_failed',
            'ADMIN_LOGIN': 'admin_login',
            'ADMIN_LOGIN_FAILED': 'admin_login_failed',
            'UNAUTHORIZED_ACCESS': 'admin_access_denied',
            'SUSPICIOUS_REQUEST': 'suspicious_request',
        }
        return type_map.get(raw_type, raw_type.lower())

    @staticmethod
    def _normalize_status(raw_status):
        """Normalize status values from SecureBank (UPPER_CASE) to SIEM internal (lowercase)."""
        if not raw_status:
            return 'info'
        status_map = {
            'SUCCESS': 'success',
            'FAILED': 'failed',
            'BLOCKED': 'blocked',
            'DENIED': 'denied',
            'LOCKED': 'locked',
        }
        return status_map.get(raw_status.upper(), raw_status.lower())

    def process_raw_event(self, raw_evt):
        """
        Normalizes, deduplicates, and passes event through Mini SIEM pipeline:
        Event -> DB -> ML Anomaly -> Rule Engine -> Risk Score -> Alert -> Incident -> SocketIO
        """
        ext_id = str(raw_evt.get('id') or raw_evt.get('event_id') or f"{raw_evt.get('timestamp')}-{raw_evt.get('source_ip')}-{raw_evt.get('event_type')}")

        # 1. Deduplication check
        existing = SecurityEvent.query.filter_by(external_id=ext_id).first()
        if existing:
            return None

        # Parse timestamp
        ts_raw = raw_evt.get('timestamp')
        try:
            if isinstance(ts_raw, str):
                ts = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
            else:
                ts = datetime.utcnow()
        except Exception:
            ts = datetime.utcnow()

        # 2. Normalize event_type and status to match SecureBank's UPPER_CASE format
        raw_event_type = raw_evt.get('event_type', 'unknown_activity')
        raw_status = raw_evt.get('status', 'info')

        # 3. Normalize and Save Security Event
        event = SecurityEvent(
            external_id=ext_id,
            source_app=raw_evt.get('source_app', 'SecureBank Lab'),
            event_type=self._normalize_event_type(raw_event_type),
            status=self._normalize_status(raw_status),
            username=raw_evt.get('username') or raw_evt.get('user'),
            source_ip=raw_evt.get('source_ip', '127.0.0.1'),
            destination_ip=raw_evt.get('destination_ip'),
            timestamp=ts,
            details=raw_evt.get('details') or raw_evt.get('metadata') or {},
            raw_data=str(raw_evt),
            processed=True
        )
        db.session.add(event)
        db.session.commit()

        # Emit Socket.IO event for live dashboard log ticker
        try:
            socketio.emit('new_event', event.to_dict())
        except Exception:
            pass

        # 3. IP Intelligence Lookup
        ip_info = get_ip_intelligence(event.source_ip)

        # 4. ML Behavioral Anomaly Detection
        anomaly_score, is_anomaly, reasoning_str, _ = anomaly_detector.analyze_event(event)
        if is_anomaly:
            try:
                socketio.emit('new_anomaly', {
                    'event_id': event.id,
                    'source_ip': event.source_ip,
                    'username': event.username,
                    'anomaly_score': anomaly_score,
                    'reasoning': reasoning_str
                })
            except Exception:
                pass

        # 5. Rule Engine Detection Evaluation (original 5 rules)
        triggered_alerts = detection_engine.evaluate_rules(event, ip_info)

        # 6. Advanced Correlation Engine (6 correlation rules)
        correlation_alerts = correlation_engine.evaluate(event)
        triggered_alerts.extend(correlation_alerts)

        # 7. Geographic Anomaly Detection (new country, impossible travel)
        geo_alerts = geo_detection_engine.evaluate(event, ip_info)
        triggered_alerts.extend(geo_alerts)

        new_alert_objs = []
        for alert_data in triggered_alerts:
            # Ensure source_ip and username are set on alert_data
            alert_data['source_ip'] = alert_data.get('source_ip') or event.source_ip
            alert_data['username'] = alert_data.get('username') or event.username

            # Create or update alert with deduplication
            alert, is_update = create_or_update_alert(
                alert_data,
                ml_anomaly_score=anomaly_score,
                ip_info=ip_info
            )
            new_alert_objs.append(alert)

            # 7. Correlate Alert into Incident (only for new alerts)
            if not is_update:
                incident = correlate_alert_into_incident(alert)
                if incident:
                    try:
                        socketio.emit('incident_updated', incident.to_dict())
                    except Exception:
                        pass

            # 8. Notifications Dispatcher (only for new alerts)
            if not is_update:
                try:
                    notification_dispatcher.dispatch_alert_notification(alert)
                except Exception as err:
                    print(f"[Collector] Notification dispatch error: {err}")

        # 10. Update IP intelligence counters asynchronously
        try:
            self._update_ip_counters(event)
        except Exception:
            pass

        return event

    def _update_ip_counters(self, event):
        """Update event/alert counts and first/last seen for IP intelligence."""
        from app.models.ip_intelligence import IPIntelligence as IPIntModel
        ip_record = IPIntModel.query.filter_by(ip_address=event.source_ip).first()
        if ip_record:
            ip_record.event_count = (IPIntModel.query.filter_by(ip_address=event.source_ip).count())
            ip_record.alert_count = Alert.query.filter_by(source_ip=event.source_ip).count()
            if not ip_record.first_seen or (event.timestamp and event.timestamp < ip_record.first_seen):
                ip_record.first_seen = event.timestamp
            if not ip_record.last_seen or (event.timestamp and event.timestamp > ip_record.last_seen):
                ip_record.last_seen = event.timestamp
            db.session.commit()

    def poll_securebank_api(self):
        """Perform HTTP GET request to SecureBank API."""
        api_url = self.app.config['SECUREBANK_API_URL']
        api_key = self.app.config['SECUREBANK_API_KEY']
        last_ts = self._get_checkpoint()

        headers = {
            'Authorization': f'Bearer {api_key}',
            'X-SIEM-Collector': 'MiniSIEM-v1.0'
        }
        # Use SecureBank's actual query param names: start_time and per_page
        params = {
            'start_time': last_ts,
            'per_page': 100
        }

        try:
            resp = requests.get(api_url, headers=headers, params=params, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                events_list = data.get('events') if isinstance(data, dict) else (data if isinstance(data, list) else [])
                
                max_ts = last_ts
                for raw in events_list:
                    processed_evt = self.process_raw_event(raw)
                    if processed_evt and processed_evt.timestamp:
                        iso_ts = processed_evt.timestamp.isoformat()
                        if iso_ts > max_ts:
                            max_ts = iso_ts

                if max_ts != last_ts:
                    self._save_checkpoint(max_ts)
        except requests.exceptions.RequestException:
            # SecureBank might be offline or not running currently; ignore silently until started
            pass
        except Exception as err:
            print(f"[SecureBank Collector] Polling error: {err}")

    def _run_loop(self):
        while self.running:
            with self.app.app_context():
                self.poll_securebank_api()
            time.sleep(self.app.config.get('SECUREBANK_POLL_INTERVAL', 5))

# Global collector instance
securebank_collector = SecureBankCollector()
