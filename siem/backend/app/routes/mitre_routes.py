from flask import Blueprint, jsonify
from app.models.mitre_technique import MitreTechnique
from app.models.alert import Alert
from app.services.auth_service import token_required

mitre_bp = Blueprint('mitre', __name__, url_prefix='/api/mitre')

@mitre_bp.route('', methods=['GET'])
@token_required
def get_mitre_matrix():
    techniques = MitreTechnique.query.all()
    
    # Calculate detection counts per MITRE technique ID
    detection_counts = {}
    alerts = Alert.query.all()
    for a in alerts:
        if a.mitre_technique_id:
            detection_counts[a.mitre_technique_id] = detection_counts.get(a.mitre_technique_id, 0) + 1

    result = []
    for t in techniques:
        item = t.to_dict()
        item['detection_count'] = detection_counts.get(t.technique_id, 0)
        result.append(item)

    return jsonify({'techniques': result}), 200
