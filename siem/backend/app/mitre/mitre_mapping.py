from app.database import db
from app.models.mitre_technique import MitreTechnique

MITRE_DATABASE = {
    'T1110': {
        'technique_id': 'T1110',
        'technique_name': 'Brute Force',
        'tactic': 'Credential Access',
        'description': 'Adversaries may use brute force techniques to attempt access to accounts when passwords or credentials are unknown or guessed.',
        'platform': 'Web Apps, Linux, Windows, SaaS'
    },
    'T1078': {
        'technique_id': 'T1078',
        'technique_name': 'Valid Accounts',
        'tactic': 'Defense Evasion, Persistence, Privilege Escalation',
        'description': 'Adversaries may obtain and use credentials of existing legitimate accounts to gain access, compromise services, or maintain persistence.',
        'platform': 'Web Apps, Linux, Windows, Cloud'
    },
    'T1068': {
        'technique_id': 'T1068',
        'technique_name': 'Exploitation for Privilege Escalation',
        'tactic': 'Privilege Escalation',
        'description': 'Adversaries may exploit software vulnerabilities or authorization flaws to elevate access levels to restricted administrative resources.',
        'platform': 'Web Apps, Linux, Windows'
    },
    'T1499': {
        'technique_id': 'T1499',
        'technique_name': 'Endpoint Denial of Service',
        'tactic': 'Impact',
        'description': 'Adversaries may conduct high-volume or automated request flooding to degrade or exhaust availability of targeted web endpoints.',
        'platform': 'Web Apps, Network'
    },
    'T1071': {
        'technique_id': 'T1071',
        'technique_name': 'Application Layer Protocol',
        'tactic': 'Command and Control',
        'description': 'Adversaries may communicate using application layer protocols to blend in with normal administrative or user web traffic.',
        'platform': 'Web Apps, Linux, Windows'
    },
    'T1190': {
        'technique_id': 'T1190',
        'technique_name': 'Exploit Public-Facing Application',
        'tactic': 'Initial Access',
        'description': 'Adversaries may attempt to exploit weakness in an Internet-facing application to cause unauthorized command execution or unauthorized data access.',
        'platform': 'Web Apps, Containers'
    }
}

def seed_mitre_techniques():
    """Ensure MITRE techniques exist in the database."""
    for tech_id, data in MITRE_DATABASE.items():
        existing = MitreTechnique.query.filter_by(technique_id=tech_id).first()
        if not existing:
            tech = MitreTechnique(
                technique_id=data['technique_id'],
                technique_name=data['technique_name'],
                tactic=data['tactic'],
                description=data['description'],
                platform=data['platform']
            )
            db.session.add(tech)
    db.session.commit()

def get_mitre_info(technique_id):
    """Retrieve details for a given technique ID."""
    if not technique_id:
        return None
    tech = MitreTechnique.query.filter_by(technique_id=technique_id).first()
    if tech:
        return tech.to_dict()
    return MITRE_DATABASE.get(technique_id)
