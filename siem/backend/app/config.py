import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mini-siem-super-secret-jwt-key-2026-soc-defense')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    
    # Primary DB: PostgreSQL. Fallback to SQLite if PostgreSQL is unavailable.
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/vaultx_siem')
    SQLITE_FALLBACK_URL = os.environ.get('SQLITE_FALLBACK_URL', 'sqlite:///vaultx_siem.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # API Key for authenticating external event ingestion (Bank → SIEM)
    SIEM_API_KEY = os.environ.get('SIEM_API_KEY', 'vaultx_siem_api_key_2026')
    
    # SecureBank collector config
    SECUREBANK_API_URL = os.environ.get('SECUREBANK_API_URL', 'http://localhost:5000/api/security-events')
    SECUREBANK_API_KEY = os.environ.get('SECUREBANK_API_KEY', 'vaultx_siem_api_key_2026')
    SECUREBANK_POLL_INTERVAL = int(os.environ.get('SECUREBANK_POLL_INTERVAL', '10'))
    
    # Notification webhooks
    DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')
    EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    
    REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'reports'))

    # Advanced Correlation Detection Thresholds
    BRUTE_FORCE_THRESHOLD = int(os.environ.get('BRUTE_FORCE_THRESHOLD', '5'))
    BRUTE_FORCE_WINDOW_MINUTES = int(os.environ.get('BRUTE_FORCE_WINDOW_MINUTES', '5'))
    PASSWORD_SPRAY_USER_THRESHOLD = int(os.environ.get('PASSWORD_SPRAY_USER_THRESHOLD', '5'))
    PASSWORD_SPRAY_WINDOW_MINUTES = int(os.environ.get('PASSWORD_SPRAY_WINDOW_MINUTES', '10'))
    DISTRIBUTED_AUTH_THRESHOLD = int(os.environ.get('DISTRIBUTED_AUTH_THRESHOLD', '5'))
    DISTRIBUTED_AUTH_WINDOW_MINUTES = int(os.environ.get('DISTRIBUTED_AUTH_WINDOW_MINUTES', '60'))
    DISTRIBUTED_AUTH_UNIQUE_IP_THRESHOLD = int(os.environ.get('DISTRIBUTED_AUTH_UNIQUE_IP_THRESHOLD', '3'))
    DISTRIBUTED_AUTH_UNIQUE_USER_THRESHOLD = int(os.environ.get('DISTRIBUTED_AUTH_UNIQUE_USER_THRESHOLD', '3'))
    MULTI_SOURCE_ACCOUNT_THRESHOLD = int(os.environ.get('MULTI_SOURCE_ACCOUNT_THRESHOLD', '3'))
    MULTI_SOURCE_ACCOUNT_WINDOW_MINUTES = int(os.environ.get('MULTI_SOURCE_ACCOUNT_WINDOW_MINUTES', '15'))
    ALERT_DEDUP_WINDOW_MINUTES = int(os.environ.get('ALERT_DEDUP_WINDOW_MINUTES', '15'))
