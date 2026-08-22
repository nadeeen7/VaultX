import requests
from flask import current_app
from app.database import db
from app.models.notification import Notification

class NotificationDispatcher:
    """Modular notification system supporting Discord, Slack, and Email channels."""

    @staticmethod
    def dispatch_alert_notification(alert):
        """Dispatch notification for HIGH and CRITICAL alerts."""
        if alert.severity not in ['HIGH', 'CRITICAL']:
            return

        discord_url = current_app.config.get('DISCORD_WEBHOOK_URL')
        slack_url = current_app.config.get('SLACK_WEBHOOK_URL')

        # 1. Discord Webhook Dispatch
        if discord_url:
            payload = {
                "embeds": [{
                    "title": f"🚨 SIEM ALERT: {alert.title}",
                    "description": alert.description,
                    "color": 15158332 if alert.severity == 'CRITICAL' else 15105570,
                    "fields": [
                        {"name": "Severity", "value": alert.severity, "inline": True},
                        {"name": "Source IP", "value": alert.source_ip, "inline": True},
                        {"name": "User", "value": alert.username or "N/A", "inline": True},
                        {"name": "Risk Score", "value": f"{alert.risk_score}/100", "inline": True},
                        {"name": "MITRE Technique", "value": alert.mitre_technique_id or "N/A", "inline": True}
                    ],
                    "footer": {"text": "Mini SIEM Defense Engine • 2026"}
                }]
            }
            try:
                res = requests.post(discord_url, json=payload, timeout=3.0)
                status = 'SENT' if res.status_code in [200, 204] else 'FAILED'
                notif = Notification(
                    alert_id=alert.id,
                    channel='discord',
                    status=status,
                    payload=payload,
                    error_message=None if status == 'SENT' else f"HTTP {res.status_code}"
                )
                db.session.add(notif)
            except Exception as err:
                notif = Notification(
                    alert_id=alert.id,
                    channel='discord',
                    status='FAILED',
                    payload=payload,
                    error_message=str(err)
                )
                db.session.add(notif)

        # 2. Slack Webhook Dispatch
        if slack_url:
            slack_payload = {
                "text": f"*🚨 SIEM ALERT [{alert.severity}]*: {alert.title}\n> {alert.description}\n*Source IP*: `{alert.source_ip}` | *User*: `{alert.username}` | *Risk Score*: `{alert.risk_score}`"
            }
            try:
                res = requests.post(slack_url, json=slack_payload, timeout=3.0)
                status = 'SENT' if res.status_code in [200, 204] else 'FAILED'
                notif = Notification(
                    alert_id=alert.id,
                    channel='slack',
                    status=status,
                    payload=slack_payload,
                    error_message=None if status == 'SENT' else f"HTTP {res.status_code}"
                )
                db.session.add(notif)
            except Exception as err:
                notif = Notification(
                    alert_id=alert.id,
                    channel='slack',
                    status='FAILED',
                    payload=slack_payload,
                    error_message=str(err)
                )
                db.session.add(notif)

        db.session.commit()

notification_dispatcher = NotificationDispatcher()
