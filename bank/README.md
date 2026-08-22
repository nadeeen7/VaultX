# SecureBank Lab

A full-stack cybersecurity training/lab banking application that generates realistic security events for SIEM consumption.

> ⚠️ **This is a training/lab application.** All data is fake. No real banking operations are performed.

## Tech Stack

- **Frontend:** React 18 + Vite + Tailwind CSS
- **Backend:** Python Flask + SQLAlchemy ORM
- **Database:** PostgreSQL
- **Authentication:** JWT + bcrypt password hashing

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- PostgreSQL 14+

### 1. Database Setup

```bash
# Create the database and user
psql -U postgres -c "CREATE USER securebank WITH PASSWORD 'securebank' CREATEDB;"
psql -U postgres -c "CREATE DATABASE securebank OWNER securebank;"
```

### 2. Backend Setup

```bash
cd securebank/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Seed the database with demo data
python seed.py

# Start the backend server
python run.py
```

The backend runs at `http://localhost:5000`.

### 3. Frontend Setup

```bash
cd securebank/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend runs at `http://localhost:5173`.

### 4. Open the Application

Visit `http://localhost:5173` in your browser.

## Test Credentials

| Role    | Username | Password   |
|---------|----------|------------|
| Admin   | admin    | Admin@123  |
| User    | alice    | Alice@123  |
| User    | bob      | Bob@123    |
| User    | charlie  | Charlie@123|
| User    | diana    | Diana@123  |
| User    | eve      | Eve@123    |

## Project Structure

```
securebank/
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── context/        # React context (auth)
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service (Axios)
│   │   └── App.jsx         # Main app with routing
│   └── ...
├── backend/                # Flask backend
│   ├── app/
│   │   ├── auth/           # JWT & password utilities
│   │   ├── logging/        # Security event logging
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routes/         # API routes (blueprints)
│   │   ├── services/       # Business logic
│   │   └── app.py          # Flask app factory
│   ├── config/             # Configuration
│   ├── seed.py             # Database seed script
│   └── run.py              # Entry point
├── .env.example            # Environment template
└── README.md
```

## API Endpoints

### Authentication
| Method | Endpoint              | Description         |
|--------|-----------------------|---------------------|
| POST   | /api/auth/register    | Register a new user |
| POST   | /api/auth/login       | Login               |
| POST   | /api/auth/logout      | Logout (auth required)|

### User
| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| GET    | /api/user/profile     | Get current user profile |
| PUT    | /api/user/profile     | Update profile           |
| POST   | /api/user/change-password | Change password      |
| GET    | /api/user/transactions| Get user transactions    |
| GET    | /api/user/login-history| Get login history      |

### Transactions
| Method | Endpoint                    | Description         |
|--------|-----------------------------|---------------------|
| POST   | /api/transactions/transfer  | Create a transfer   |

### Admin
| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| POST   | /api/admin/login            | Admin login              |
| GET    | /api/admin/users            | List all users           |
| POST   | /api/admin/users/:id/toggle-status | Enable/disable user |
| GET    | /api/admin/transactions     | List all transactions    |
| GET    | /api/admin/security-events  | List security events     |
| GET    | /api/admin/login-activity   | List login attempts      |
| GET    | /api/admin/stats            | System statistics        |

### Security Events (SIEM Endpoint)
| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| GET    | /api/security-events        | Query security events    |

Supports query parameters: `page`, `per_page`, `event_type`, `status`, `user_id`, `username`, `source_ip`, `start_time`, `end_time`

## Security Events Generated

Every important action generates a structured security event:

- `LOGIN_SUCCESS` / `LOGIN_FAILED`
- `LOGOUT`
- `ACCOUNT_CREATED`
- `ACCOUNT_LOCKED`
- `TRANSFER_CREATED` / `TRANSFER_FAILED`
- `PASSWORD_CHANGE` / `PASSWORD_CHANGE_FAILED`
- `ADMIN_LOGIN` / `ADMIN_LOGIN_FAILED`
- `UNAUTHORIZED_ACCESS`
- `SUSPICIOUS_REQUEST`

## SIEM Integration

The `GET /api/security-events` endpoint returns structured JSON events suitable for consumption by a separate SIEM application:

```json
{
  "events": [
    {
      "event_id": "uuid",
      "timestamp": "ISO8601",
      "event_type": "LOGIN_FAILED",
      "user_id": "...",
      "username": "...",
      "source_ip": "...",
      "endpoint": "/api/auth/login",
      "http_method": "POST",
      "status": "FAILED",
      "metadata": {}
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 100,
  "pages": 1
}
```

## Security Controls

- Password hashing (bcrypt)
- JWT authentication
- Role-based authorization (user/admin)
- Account lockout after failed attempts
- Input validation
- CORS configuration
- Structured security event logging
- Audit trail logging
- Suspicious request detection
