import os
from flask import Blueprint, send_file, Response, jsonify, g
from app.services.report_generator import generate_pdf_report, generate_csv_export, generate_json_export
from app.services.auth_service import token_required
from app.services.audit_service import log_audit_action
from app.config import Config

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/pdf', methods=['GET'])
@token_required
def download_pdf_report():
    report_filename = "mini_siem_executive_report.pdf"
    output_path = os.path.join(Config.REPORTS_DIR, report_filename)
    
    generate_pdf_report(output_path)

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action="Generated PDF Executive Report"
    )

    return send_file(output_path, as_attachment=True, download_name=report_filename)

@report_bp.route('/csv', methods=['GET'])
@token_required
def download_csv_report():
    csv_data = generate_csv_export()
    
    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action="Exported Security Data as CSV"
    )

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=mini_siem_events_export.csv"}
    )

@report_bp.route('/json', methods=['GET'])
@token_required
def download_json_report():
    json_data = generate_json_export()
    
    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action="Exported Security Data as JSON"
    )

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=mini_siem_security_dump.json"}
    )
