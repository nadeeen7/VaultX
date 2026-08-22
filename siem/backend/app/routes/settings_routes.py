from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models.setting import Setting
from app.services.auth_service import token_required, roles_required
from app.services.audit_service import log_audit_action

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

DEFAULT_SETTINGS = {
    # Original detection thresholds
    'brute_force_threshold': ('5', 'Number of failed logins required to trigger Brute Force alert'),
    'brute_force_window_mins': ('5', 'Time window (minutes) for brute force detection'),
    'admin_abuse_threshold': ('3', 'Number of unauthorized admin attempts to trigger privilege abuse alert'),
    'admin_abuse_window_mins': ('10', 'Time window (minutes) for admin abuse detection'),
    'high_freq_threshold': ('20', 'Number of requests in 1 min to trigger high request frequency alert'),
    # Advanced correlation detection thresholds
    'password_spray_user_threshold': ('5', 'Number of distinct usernames to trigger Password Spraying alert'),
    'password_spray_window_mins': ('10', 'Time window (minutes) for password spraying detection'),
    'distributed_auth_threshold': ('5', 'Minimum total failures to trigger Distributed Auth Anomaly'),
    'distributed_auth_window_mins': ('60', 'Time window (minutes) for distributed authentication detection'),
    'distributed_auth_unique_ip_threshold': ('3', 'Minimum distinct source IPs for distributed auth anomaly'),
    'distributed_auth_unique_user_threshold': ('3', 'Minimum distinct usernames for distributed auth anomaly'),
    'multi_source_account_threshold': ('3', 'Minimum distinct source IPs targeting one account'),
    'multi_source_account_window_mins': ('15', 'Time window (minutes) for multi-source account attack detection'),
    'suspicious_success_window_mins': ('15', 'Time window (minutes) to check for failures before a success'),
    'suspicious_success_fail_threshold': ('3', 'Minimum failures before a success triggers alert'),
    'compromise_window_mins': ('30', 'Time window (minutes) for account compromise detection'),
    'compromise_fail_threshold': ('3', 'Minimum failures before a success+transfer triggers compromise alert'),
    # System settings
    'securebank_poll_interval': ('5', 'Polling interval (seconds) for SecureBank log collector'),
    'discord_webhook_url': ('', 'Discord channel webhook URL for alert notifications'),
    'slack_webhook_url': ('', 'Slack webhook URL for alert notifications'),
    # Geographic detection thresholds
    'new_country_cooldown_mins': ('60', 'Cooldown (minutes) for New Country for User alerts'),
    'impossible_travel_window_hours': ('2', 'Time window (hours) to check for impossible travel'),
    'impossible_travel_speed_kmh': ('900', 'Speed threshold (km/h) above which travel is considered impossible'),
    'geo_cache_hours': ('24', 'Cache duration (hours) for IP geolocation lookups'),
}

@settings_bp.route('', methods=['GET'])
@token_required
def get_settings():
    settings = Setting.query.all()
    setting_map = {s.key: s.to_dict() for s in settings}

    # Fill default fallbacks
    for key, (val, desc) in DEFAULT_SETTINGS.items():
        if key not in setting_map:
            setting_map[key] = {
                'key': key,
                'value': val,
                'description': desc,
                'updated_at': None
            }

    return jsonify({'settings': list(setting_map.values())}), 200

@settings_bp.route('', methods=['PUT', 'POST'])
@token_required
@roles_required('Admin')
def update_settings():
    data = request.get_json() or {}
    updated = []

    for key, val in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if not setting:
            desc = DEFAULT_SETTINGS.get(key, ('', 'System configuration setting'))[1]
            setting = Setting(key=key, value=str(val), description=desc)
            db.session.add(setting)
        else:
            setting.value = str(val)
        updated.append(key)

    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action="Updated SIEM Detection & System Settings",
        details={'keys_updated': updated}
    )

    return jsonify({'message': 'Settings updated successfully'}), 200
