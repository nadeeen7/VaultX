"""
Database cleanup script for vaultx_siem
Removes ALL fake/demo/seeded security events, alerts, and incidents.
Preserves: table structure, MITRE techniques, SOC admin/analyst/viewer users, settings.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.database import db
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.incident import Incident, IncidentEvent
from app.models.ml_anomaly import MLAnomaly
from app.models.ip_intelligence import IPIntelligence
from app.models.audit_log import AuditLog
from app.models.notification import Notification


def clear_demo_data():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("SIEM Database Cleanup — Removing Demo/Seeded Data")
        print("=" * 60)

        # Count before cleanup
        event_count = SecurityEvent.query.count()
        alert_count = Alert.query.count()
        incident_count = Incident.query.count()
        incident_event_count = IncidentEvent.query.count()
        anomaly_count = MLAnomaly.query.count()
        ip_intel_count = IPIntelligence.query.count()
        audit_count = AuditLog.query.count()
        notification_count = Notification.query.count()

        print(f"\nCurrent record counts:")
        print(f"  Security Events:    {event_count}")
        print(f"  Alerts:             {alert_count}")
        print(f"  Incidents:          {incident_count}")
        print(f"  Incident Events:    {incident_event_count}")
        print(f"  ML Anomalies:       {anomaly_count}")
        print(f"  IP Intelligence:    {ip_intel_count}")
        print(f"  Audit Logs:         {audit_count}")
        print(f"  Notifications:      {notification_count}")

        if event_count == 0 and alert_count == 0 and incident_count == 0:
            print("\nOK Database is already clean. No demo data to remove.")
            return

        print(f"\nWARNING: This will DELETE all {event_count} events, {alert_count} alerts, {incident_count} incidents,")
        print(f"   {anomaly_count} ML anomalies, {ip_intel_count} IP records, {audit_count} audit logs,")
        print(f"   and {notification_count} notifications.")
        print(f"\nTable structure, MITRE techniques, and SOC users will be PRESERVED.")

        confirm = input("\nType 'yes' to confirm cleanup: ").strip().lower()
        if confirm != 'yes':
            print("Cleanup cancelled.")
            return

        # Delete in order (respect foreign key constraints)
        print("\nCleaning up...")

        # 1. Delete incident_events (has FK to incidents and alerts)
        deleted = IncidentEvent.query.delete()
        print(f"  Deleted {deleted} incident events")

        # 2. Delete incidents
        deleted = Incident.query.delete()
        print(f"  Deleted {deleted} incidents")

        # 3. Delete alerts
        deleted = Alert.query.delete()
        print(f"  Deleted {deleted} alerts")

        # 4. Delete ML anomalies
        deleted = MLAnomaly.query.delete()
        print(f"  Deleted {deleted} ML anomalies")

        # 5. Delete security events
        deleted = SecurityEvent.query.delete()
        print(f"  Deleted {deleted} security events")

        # 6. Delete IP intelligence cache
        deleted = IPIntelligence.query.delete()
        print(f"  Deleted {deleted} IP intelligence records")

        # 7. Delete audit logs
        deleted = AuditLog.query.delete()
        print(f"  Deleted {deleted} audit logs")

        # 8. Delete notifications
        deleted = Notification.query.delete()
        print(f"  Deleted {deleted} notifications")

        # Reset the collector checkpoint
        from app.models.setting import Setting
        checkpoint = Setting.query.filter_by(key='last_event_timestamp').first()
        if checkpoint:
            checkpoint.value = '1970-01-01T00:00:00Z'
            print("  Reset collector checkpoint")

        db.session.commit()

        print("\n" + "=" * 60)
        print("Database cleanup complete!")
        print("=" * 60)
        print("\nPreserved:")
        print("  - Table structure (all columns, indexes, relationships)")
        print("  - MITRE ATT&CK techniques reference data")
        print("  - SOC users (admin, analyst, viewer)")
        print("  - Application settings")
        print("\nThe SIEM will now only show real events from VaultX Bank.")


if __name__ == '__main__':
    clear_demo_data()
