import os
import json
import csv
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.mitre_technique import MitreTechnique
from app.models.ip_intelligence import IPIntelligence

def generate_pdf_report(output_path):
    """Generates an executive SOC security report as a PDF document."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom SOC Styles
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=colors.HexColor('#0F172A'), spaceAfter=10)
    subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontSize=11, leading=14, textColor=colors.HexColor('#64748B'), spaceAfter=15)
    h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1E293B'), spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=9, leading=12, textColor=colors.HexColor('#334155'))

    story = []

    # Title & Header
    story.append(Paragraph("MINI SIEM • EXECUTIVE SECURITY REPORT", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Classification: CONFIDENTIAL", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=15))

    # Executive Summary Stats
    total_events = SecurityEvent.query.count()
    total_alerts = Alert.query.count()
    total_incidents = Incident.query.count()
    critical_alerts = Alert.query.filter_by(severity='CRITICAL').count()
    high_alerts = Alert.query.filter_by(severity='HIGH').count()

    story.append(Paragraph("1. Executive Summary", h2_style))
    exec_text = (
        f"During the current monitoring period, Mini SIEM collected and analyzed <b>{total_events}</b> security events "
        f"from SecureBank Lab. Detection logic generated <b>{total_alerts}</b> alerts (<b>{critical_alerts} CRITICAL</b>, "
        f"<b>{high_alerts} HIGH</b>), leading to <b>{total_incidents}</b> correlated incidents."
    )
    story.append(Paragraph(exec_text, body_style))
    story.append(Spacer(1, 10))

    # Summary Metrics Table
    metrics_data = [
        ['Total Security Events', 'Total Alerts Generated', 'Critical / High Alerts', 'Active Incidents'],
        [str(total_events), str(total_alerts), f"{critical_alerts} / {high_alerts}", str(total_incidents)]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 130, 130, 130])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 15))

    # Top Alerts Section
    story.append(Paragraph("2. Critical & High Security Detections", h2_style))
    recent_alerts = Alert.query.order_by(Alert.risk_score.desc()).limit(8).all()

    alert_table_data = [['ID', 'Severity', 'Title', 'Source IP', 'User', 'Risk Score', 'Status']]
    for a in recent_alerts:
        alert_table_data.append([
            f"ALT-{a.id}",
            a.severity,
            a.title[:30] + ('...' if len(a.title) > 30 else ''),
            a.source_ip,
            a.username or 'N/A',
            f"{a.risk_score}",
            a.status
        ])

    if len(alert_table_data) > 1:
        t_alerts = Table(alert_table_data, colWidths=[45, 55, 160, 85, 75, 50, 50])
        t_alerts.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        story.append(t_alerts)
    else:
        story.append(Paragraph("No alerts recorded during this timeframe.", body_style))

    story.append(Spacer(1, 15))

    # Incidents & Defensive Recommendations
    story.append(Paragraph("3. SOC Defensive Recommendations", h2_style))
    recs = [
        "• Enforce Multi-Factor Authentication (MFA) across all administrative accounts.",
        "• Apply rate limiting rules (max 15 requests/min per IP) on authentication endpoints.",
        "• Block malicious external source IPs at network perimeter / WAF level.",
        "• Conduct immediate credential rotation for compromised accounts identified in Incident records."
    ]
    for r in recs:
        story.append(Paragraph(r, body_style))
        story.append(Spacer(1, 3))

    doc.build(story)
    return output_path

def generate_csv_export():
    """Exports all alerts and events as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Record Type', 'ID', 'Timestamp', 'Title / Event', 'Severity / Status', 'Source IP', 'User', 'Risk Score', 'MITRE ID'])

    events = SecurityEvent.query.order_by(SecurityEvent.timestamp.desc()).limit(200).all()
    for e in events:
        writer.writerow(['EVENT', e.id, e.timestamp.isoformat() if e.timestamp else '', e.event_type, e.status, e.source_ip, e.username or '', '', ''])

    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(200).all()
    for a in alerts:
        writer.writerow(['ALERT', a.id, a.timestamp.isoformat() if a.timestamp else '', a.title, a.severity, a.source_ip, a.username or '', a.risk_score, a.mitre_technique_id or ''])

    return output.getvalue()

def generate_json_export():
    """Exports full SIEM state dump as JSON dictionary."""
    events = [e.to_dict() for e in SecurityEvent.query.order_by(SecurityEvent.timestamp.desc()).limit(100).all()]
    alerts = [a.to_dict() for a in Alert.query.order_by(Alert.timestamp.desc()).limit(100).all()]
    incidents = [i.to_dict() for i in Incident.query.order_by(Incident.created_at.desc()).limit(50).all()]

    return json.dumps({
        'exported_at': datetime.utcnow().isoformat(),
        'summary': {
            'total_events': SecurityEvent.query.count(),
            'total_alerts': Alert.query.count(),
            'total_incidents': Incident.query.count()
        },
        'events': events,
        'alerts': alerts,
        'incidents': incidents
    }, indent=2)
