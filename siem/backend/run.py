import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.database import socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"==================================================")
    print(f"[SENTINELSIEM] SOC BACKEND RUNNING ON PORT {port}")
    print(f"==================================================")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
