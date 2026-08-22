# VaultX — Integrated Cybersecurity Training Platform

A fully functional **Banking Application** + **SIEM (Security Information & Event Management)** system. The Bank generates real security events on every user action, which are pushed to SentinelSIEM for real-time monitoring, detection, alerting, and incident correlation.

## Architecture

```
                    VAULTX
                       │
          ┌────────────┴────────────┐
          │                         │
       BANK                    SENTINELSIEM
          │                         │
     React/Vite                 React/Vite
          │                         │
       Flask                     Flask
          │                         │
     PostgreSQL                PostgreSQL
          │                         ▲
          │                         │
          └──── Security Events ────┘
```

### Event Flow

1. User performs an action in the Bank (login, transfer, etc.)
2. Bank Flask backend processes the request
3. Security event is logged to Bank's PostgreSQL database
4. Bank backend **pushes** the event to SIEM via `POST /api/events` (background thread)
5. SIEM stores the event in its own PostgreSQL database
6. SIEM's detection engine analyzes the event against rules
7. Alerts are generated if thresholds are exceeded
8. Socket.IO broadcasts updates to the SIEM dashboard in real-time

### Dual Collection

- **Primary (Push):** Bank pushes events to SIEM immediately via HTTP POST
- **Backup (Poll):** SIEM polls Bank's `GET /api/security-events` every 10 seconds as a fallback

## Required PostgreSQL Databases

Create two databases before starting:

```sql
CREATE USER vaultx WITH PASSWORD 'vaultx';
CREATE DATABASE vaultx_bank OWNER vaultx;
CREATE DATABASE vaultx_siem OWNER vaultx;
```

Or with superuser:

```sql
CREATE DATABASE vaultx_bank;
CREATE DATABASE vaultx_siem;
```

## Environment Variables

### Bank Backend (`bank/backend/.env`)

```env
DATABASE_URL=postgresql://vaultx:vaultx@localhost:5432/vaultx_bank
JWT_SECRET_KEY=change-this-to-a-random-secret-key
SIEM_API_URL=http://localhost:5001
SIEM_API_KEY=vaultx_siem_api_key_2026
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-secret-key
CORS_ORIGINS=http://localhost:5173
```

### Bank Frontend (`bank/frontend/.env`)

```env
VITE_API_URL=http://localhost:5000
```

### SIEM Backend (`siem/backend/.env`)

```env
DATABASE_URL=postgresql://vaultx:vaultx@localhost:5432/vaultx_siem
SECRET_KEY=change-this-to-a-random-secret-key
JWT_SECRET_KEY=change-this-to-another-random-secret-key
SIEM_API_KEY=vaultx_siem_api_key_2026
SECUREBANK_API_URL=http://localhost:5000/api/security-events
SECUREBANK_POLL_INTERVAL=10
PORT=5001
```

### SIEM Frontend (`siem/frontend/.env`)

```env
VITE_API_URL=http://localhost:5001
```

## How to Run

### 1. Start Bank Backend

```powershell
cd bank\backend
pip install -r requirements.txt
python run.py
```

Runs on **http://localhost:5000**

### 2. Start Bank Frontend

```powershell
cd bank\frontend
npm install
npm run dev
```

Runs on **http://localhost:5173**

### 3. Start SIEM Backend

```powershell
cd siem\backend
pip install -r requirements.txt
python run.py
```

Runs on **http://localhost:5001**

### 4. Start SIEM Frontend

```powershell
cd siem\frontend
npm install
npm run dev -- --port 5174
```

Runs on **http://localhost:5174**

## Ports

| Service             | Port   | URL                            |
|---------------------|--------|--------------------------------|
| Bank Frontend       | 5173   | http://localhost:5173           |
| Bank Backend        | 5000   | http://localhost:5000           |
| SIEM Frontend       | 5174   | http://localhost:5174           |
| SIEM Backend        | 5001   | http://localhost:5001           |

## API Endpoints

### Bank Backend

| Method | Endpoint                       | Auth    | Description                  |
|--------|--------------------------------|---------|------------------------------|
| GET    | /api/health                    | None    | Health check with DB status  |
| POST   | /api/auth/register             | None    | Register new user            |
| POST   | /api/auth/login                | None    | Login                        |
| POST   | /api/auth/logout               | JWT     | Logout                       |
| GET    | /api/user/profile              | JWT     | Get user profile + account   |
| PUT    | /api/user/profile              | JWT     | Update profile               |
| POST   | /api/user/change-password      | JWT     | Change password              |
| GET    | /api/user/transactions         | JWT     | Transaction history          |
| GET    | /api/user/login-history        | JWT     | Login history                |
| POST   | /api/transactions/transfer     | JWT     | Create transfer              |
| POST   | /api/admin/login               | None    | Admin login                  |
| GET    | /api/admin/stats               | Admin   | System statistics            |
| GET    | /api/admin/users               | Admin   | All users                    |
| POST   | /api/admin/users/<id>/toggle   | Admin   | Enable/disable user          |
| GET    | /api/admin/transactions        | Admin   | All transactions             |
| GET    | /api/admin/security-events     | Admin   | Security events              |
| GET    | /api/admin/login-activity      | Admin   | Login activity               |
| GET    | /api/security-events           | None    | Public events (for SIEM)     |

### SIEM Backend

| Method | Endpoint                       | Auth    | Description                  |
|--------|--------------------------------|---------|------------------------------|
| GET    | /api/health                    | None    | Health check                 |
| POST   | /api/events                    | API Key | Ingest security events       |
| GET    | /api/events                    | JWT     | List events                  |
| GET    | /api/events/<id>               | JWT     | Event detail                 |
| POST   | /api/auth/login                | None    | SIEM login                   |
| GET    | /api/auth/me                   | JWT     | Current user                 |
| GET    | /api/alerts                    | JWT     | List alerts                  |
| GET    | /api/alerts/<id>               | JWT     | Alert detail + MITRE + IP    |
| PATCH  | /api/alerts/<id>/status        | JWT     | Update alert status          |
| POST   | /api/alerts/<id>/assign        | JWT     | Assign alert                 |
| POST   | /api/alerts/<id>/notes         | JWT     | Add analyst note             |
| GET    | /api/incidents                 | JWT     | List incidents               |
| GET    | /api/incidents/<id>            | JWT     | Incident detail + timeline   |
| GET    | /api/incidents/timeline        | JWT     | Attack timeline              |
| GET    | /api/analytics/dashboard       | JWT     | Dashboard metrics + charts   |
| GET    | /api/analytics/ml              | JWT     | ML anomaly data              |
| GET    | /api/mitre                     | JWT     | MITRE ATT&CK matrix          |
| GET    | /api/ip-intelligence           | JWT     | Cached IP data               |
| GET    | /api/ip-intelligence/<ip>      | JWT     | IP lookup                    |
| GET    | /api/reports/pdf               | JWT     | PDF report                   |
| GET    | /api/reports/csv               | JWT     | CSV export                   |
| GET    | /api/reports/json              | JWT     | JSON dump                    |
| GET    | /api/settings                  | JWT     | Detection settings           |
| POST   | /api/settings                  | JWT     | Update settings              |
| GET    | /api/users                     | Admin   | SIEM users                   |
| POST   | /api/users                     | Admin   | Create SIEM user             |
| PATCH  | /api/users/<id>/role           | Admin   | Update role                  |
| POST   | /api/test/inject-scenario      | None    | Test event injection         |

## Default Credentials

### Bank

| Role  | Username | Password     |
|-------|----------|--------------|
| Admin | admin    | Admin@123    |
| User  | (register via UI) | — |

**Note:** No fake users are pre-seeded. Register a new account through the Bank UI. The initial balance is $5,000.00.

### SIEM

| Role              | Username | Password    |
|-------------------|----------|-------------|
| Admin             | admin    | admin123    |
| Security Analyst  | analyst | analyst123  |
| Viewer            | viewer   | viewer123   |

## Security Features

### Bank

- **JWT Authentication** with configurable token expiry
- **Password hashing** with bcrypt
- **Account lockout** after 5 failed login attempts (15-minute lockout)
- **Role-based access control** (user, admin)
- **Input validation** on all endpoints
- **SQL injection prevention** via SQLAlchemy ORM
- **CORS** restricted to allowed origins
- **Suspicious request detection** (SQL injection, XSS patterns)

### Bank → SIEM

- **API key authentication** via `X-API-Key` header
- **Non-blocking push** (background thread) — Bank never fails due to SIEM being offline
- **Deduplication** by event_id in SIEM

### SIEM

- **Detection Rules:**
  - Brute Force Attack (repeated failed logins)
  - Account Compromise (failed → success pattern)
  - Privilege Abuse (unauthorized admin access)
  - High Request Frequency (automated activity)
  - New Login Source (unusual IP)
- **ML Anomaly Detection** via scikit-learn Isolation Forest
- **Risk Scoring** with transparent factor breakdown
- **Incident Correlation** — related alerts grouped into incidents
- **MITRE ATT&CK mapping** for each detection
- **IP Intelligence** with GeoIP lookups

## Security Events Generated by Bank

| Event Type           | When                                    |
|---------------------|-----------------------------------------|
| LOGIN_SUCCESS       | Successful login                        |
| LOGIN_FAILED        | Failed login attempt                    |
| ACCOUNT_LOCKED      | Account locked after max attempts       |
| LOGOUT              | User logout                             |
| ACCOUNT_CREATED     | New user registration                   |
| TRANSFER_CREATED    | Successful money transfer               |
| TRANSFER_FAILED     | Failed transfer (insufficient funds)    |
| PASSWORD_CHANGE     | Password changed                        |
| PASSWORD_CHANGE_FAILED | Failed password change                |
| ADMIN_LOGIN         | Admin login                             |
| ADMIN_LOGIN_FAILED  | Admin login failed                      |
| UNAUTHORIZED_ACCESS | Non-admin accessing admin routes        |
| SUSPICIOUS_REQUEST  | Potential injection/XSS attempt         |

## No Fake Data

This application uses **no fake or hardcoded data**. All data comes from:
- User actions through the Bank UI
- Database queries against PostgreSQL
- Events generated by actual user interactions

If the database is empty, the UI displays "No data available" instead of inventing data.

The only pre-seeded data are:
- Default SIEM admin/analyst/viewer accounts
- MITRE ATT&CK technique definitions

## Technology Stack

| Component    | Technology                                    |
|-------------|-----------------------------------------------|
| Bank Frontend  | React 18, Vite, Tailwind CSS, React Router, Axios |
| Bank Backend   | Python, Flask, SQLAlchemy, PostgreSQL, JWT, bcrypt |
| SIEM Frontend  | React 18, Vite, Tailwind CSS, Recharts, Socket.IO Client |
| SIEM Backend   | Python, Flask, Flask-SocketIO, SQLAlchemy, PostgreSQL, scikit-learn |
| Database       | PostgreSQL (with SQLite fallback for SIEM)    |
