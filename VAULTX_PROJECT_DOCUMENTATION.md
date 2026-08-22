# VaultX — Complete Technical Documentation & Learning Guide

> A cybersecurity project demonstrating real-time security event monitoring,
> detection, and alerting for a banking application using a SIEM system.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Why This Project Exists](#2-why-this-project-exists)
3. [Complete Architecture](#3-complete-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Folder Structure](#5-project-folder-structure)
6. [Bank Application](#6-bank-application)
7. [Bank Database](#7-bank-database)
8. [Authentication Flow](#8-authentication-flow)
9. [Transaction Flow](#9-transaction-flow)
10. [Security Event System](#10-security-event-system)
11. [Bank → SIEM Communication](#11-bank--siem-communication)
12. [SIEM Application](#12-siem-application)
13. [SIEM Database](#13-siem-database)
14. [SIEM Detection Engine](#14-siem-detection-engine)
15. [Alert Generation](#15-alert-generation)
16. [ML Anomaly Detection](#16-ml-anomaly-detection)
17. [Real-Time System (Socket.IO)](#17-real-time-system-socketio)
18. [API Documentation](#18-api-documentation)
19. [Environment Variables](#19-environment-variables)
20. [Database Setup](#20-database-setup)
21. [Installation Guide](#21-installation-guide)
22. [How to Run](#22-how-to-run)
23. [End-to-End Examples](#23-end-to-end-examples)
24. [Failure Scenarios](#24-failure-scenarios)
25. [Troubleshooting Guide](#25-troubleshooting-guide)
26. [Testing Guide](#26-testing-guide)
27. [Security Concepts Used](#27-security-concepts-used)
28. [Learning Roadmap](#28-learning-roadmap)
29. [Interview Preparation](#29-interview-preparation)
30. [Code Explanation](#30-code-explanation)
31. [Data Flow Diagrams](#31-data-flow-diagrams)
32. [Glossary](#32-glossary)
33. [Final Summary](#33-final-summary)

---

# 1. Project Overview

## What is VaultX?

VaultX is a **full-stack cybersecurity project** that consists of two connected web applications:

1. **VaultX Bank** — A simulated online banking platform
2. **SentinelSIEM** — A Security Information and Event Management system

Together, they demonstrate how a real SOC (Security Operations Center) monitors
a live banking application for threats, detects attacks, and generates alerts.

## Simple Explanation

Imagine you own a bank. Every time someone logs in, transfers money, or tries to
access an account, you want to keep a record of it. But not just any record — you
want a system that **automatically watches** all this activity and **raises an alarm**
when something suspicious happens, like someone trying to guess a password 5 times
in a row.

That is exactly what VaultX does:

- The **Bank** is where users log in, check balances, and transfer money.
- The **SIEM** is the security team's dashboard that watches everything the Bank does
  and generates alerts when threats are detected.

## Technical Explanation

VaultX is a **distributed event-driven monitoring system** that implements:

- A RESTful banking API (Flask) with JWT authentication and role-based access control
- Real-time security event generation and logging
- An asynchronous event pipeline (Bank → SIEM push via HTTP, SIEM pull via polling)
- A rule-based detection engine with 5 configurable detection rules
- An advanced correlation engine with 6 additional correlation rules (Password Spraying, Distributed Auth, Multi-Source Attack, etc.)
- An ML-based anomaly detection system (Isolation Forest)
- Risk scoring with transparent factor breakdown
- Incident correlation and grouping
- Real-time dashboard updates via Socket.IO (WebSocket)
- MITRE ATT&CK technique mapping
- IP geolocation intelligence
- Full audit trail logging
- PDF/CSV/JSON report generation
- Alert cooldown mechanism to prevent duplicate alerts

## Main Users

| User | System | Purpose |
|------|--------|---------|
| Bank customer | Bank | Log in, check balance, transfer money |
| Bank admin | Bank | Manage users, view all transactions, monitor security |
| SOC Analyst | SIEM | Monitor security events, investigate alerts |
| SOC Admin | SIEM | Full access to all SIEM features, user management |

## Technologies

| Category | Technologies |
|----------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios, Recharts, Socket.IO Client, Lucide React |
| Backend | Python Flask, Flask-CORS, Flask-SQLAlchemy, Flask-SocketIO, Flask-Bcrypt |
| Database | PostgreSQL (with SQLite fallback for SIEM) |
| Authentication | JWT (PyJWT), bcrypt password hashing |
| ML/AI | scikit-learn (Isolation Forest), NumPy |
| Communication | REST API, HTTP, WebSocket (Socket.IO) |

---

# 2. Why This Project Exists

## The Cybersecurity Problem

Banking applications are prime targets for cybercriminals. Common attacks include:

- **Brute Force Attacks**: An attacker tries hundreds of password combinations
  to break into a user's account.
- **Credential Stuffing**: An attacker uses leaked username/password pairs from
  other breaches to log in.
- **Privilege Escalation**: An attacker with limited access tries to gain admin
  privileges.
- **Account Takeover**: After a successful brute force, the attacker transfers
  money out.
- **Suspicious Transactions**: Unusual transfer patterns may indicate fraud.

## Why Monitoring Matters

Without a SIEM, a bank would have no centralized way to:

- See all security events in one place
- Detect patterns like "5 failed logins from the same IP"
- Get alerted before damage is done
- Investigate what happened after an incident
- Prove compliance with security regulations

## How VaultX Demonstrates These Concepts

VaultX creates a **complete feedback loop**:

1. A user performs an action in the Bank (login, transfer, etc.)
2. The Bank backend creates a **security event** and stores it in its database
3. The event is simultaneously **pushed to the SIEM** via HTTP API
4. The SIEM's **background collector** also **polls** the Bank for new events
5. Each event passes through the **detection engine** (5 rules)
6. Each event passes through the **ML anomaly detector** (Isolation Forest)
7. If a rule or anomaly threshold is triggered, an **alert** is created
8. Alerts are correlated into **incidents** (grouping related alerts)
9. The SIEM dashboard updates in **real-time** via Socket.IO
10. An advanced correlation engine evaluates 6 additional patterns (Password Spraying, Distributed Auth, Multi-Source Attack, etc.)
11. The SOC analyst sees the alert and can investigate

This is exactly how a real SOC operates, just on a smaller scale.

---

# 3. Complete Architecture

## High-Level Architecture

```
                    ┌─────────────────────────────┐
                    │        Bank Frontend         │
                    │    React + Vite + Tailwind   │
                    │    http://localhost:5173     │
                    └────────────┬────────────────┘
                                 │ REST API (HTTP)
                    ┌────────────▼────────────────┐
                    │        Bank Backend          │
                    │    Flask + SQLAlchemy        │
                    │    http://localhost:5000     │
                    └──────┬──────────┬───────────┘
                           │          │
                ┌──────────▼──┐   ┌───▼──────────────────────┐
                │   Bank DB   │   │  Security Events         │
                │  PostgreSQL │   │  (push via HTTP POST)    │
                │vaultx_bank  │   │  + Audit Logs            │
                └─────────────┘   └───────────┬──────────────┘
                                               │
                                               │  POST /api/events
                                               │  (X-API-Key header)
                                               ▼
                    ┌─────────────────────────────┐
                    │        SIEM Backend          │
                    │    Flask + SocketIO          │
                    │    http://localhost:5001     │
                    └──┬────┬────┬────┬──────┬────┘
                       │    │    │    │      │
          ┌────────────┘    │    │    │      └────────────┐
          │                 │    │    │                   │
   ┌──────▼───┐    ┌───────▼┐  │  ┌─▼──────────┐  ┌────▼──────────┐
   │ SIEM DB  │    │Detection│  │  │ ML Anomaly │  │ Socket.IO     │
   │PostgreSQL│    │ Engine  │  │  │ Detector   │  │ Real-Time     │
   │vaultx_siem    │(5 rules)│  │  │(IsoForest) │  │ Broadcast     │
   └──────────┘    └────────┘  │  └────────────┘  └───────┬───────┘
                               │                          │
                      ┌────────▼──────┐         ┌──────────▼────────┐
                      │ Correlation   │         │  SIEM Frontend    │
                      │ Engine (6     │         │  React + Vite     │
                      │ rules)        │         │  http://localhost:5174
                      └───────────────┘         └───────────────────┘
                      ┌───────────────┐
                      │ Incident      │
                      │ Correlation   │
                      └───────────────┘
```

## What Happens to Data at Every Stage

1. **User Action**: User clicks "Login" in the Bank React frontend
2. **Bank Frontend**: React sends `POST /api/auth/login` with credentials
3. **Bank Backend**: Flask validates credentials, creates JWT, creates a `SecurityEvent` record in `vaultx_bank`
4. **SIEM Push**: A background thread sends the event to SIEM via `POST http://localhost:5001/api/events`
5. **SIEM Collector** (also polling): The SIEM's background collector polls `GET /api/security-events` from the Bank every 10 seconds
6. **SIEM Processing Pipeline**:
   - Deduplication check (has this event_id been seen before?)
   - Normalize event type (LOGIN_FAILED → login_failed)
   - Save to `vaultx_siem` database
   - Emit Socket.IO `new_event` to connected browsers
   - IP Intelligence lookup (geolocation via ip-api.com)
   - ML Anomaly Detection (feature extraction + Isolation Forest)
   - Detection Rule Engine (5 basic rules)
   - Advanced Correlation Engine (6 correlation rules)
   - Risk Score Calculation (transparent composite score)
   - Alert Creation (if rule triggers)
   - Incident Correlation (group alerts into incidents)
   - Alert Cooldown (prevent duplicate alerts within cooldown window)
   - Notification Dispatch (Discord/Slack webhooks for HIGH/CRITICAL)

---

# 4. Technology Stack

| Component | Technology | Why It Is Used |
|-----------|-----------|---------------|
| **Bank Frontend** | React 18 + Vite | Fast, modern UI framework with hot-reloading during development |
| **Bank Frontend Styling** | Tailwind CSS | Utility-first CSS for rapid, professional UI development |
| **Bank Frontend HTTP** | Axios | Promise-based HTTP client for API calls with interceptors for JWT |
| **Bank Frontend Routing** | React Router v6 | Client-side routing for SPA navigation between pages |
| **Bank Backend** | Python Flask | Lightweight web framework ideal for REST APIs |
| **Bank ORM** | SQLAlchemy (Flask-SQLAlchemy) | Python ORM that maps database tables to Python objects |
| **Bank Auth** | JWT (PyJWT) + bcrypt | Stateless authentication (JWT) with secure password hashing (bcrypt) |
| **SIEM Frontend** | React 18 + Vite | Same stack as Bank for consistency |
| **SIEM Charts** | Recharts | React charting library for dashboard visualizations |
| **SIEM Real-Time** | Socket.IO Client | WebSocket-based real-time event streaming to the browser |
| **SIEM Backend** | Flask + Flask-SocketIO | REST API + WebSocket server in one process |
| **SIEM Password Hashing** | Flask-Bcrypt | Bcrypt integration for SIEM user passwords |
| **SIEM ML** | scikit-learn (Isolation Forest) | Unsupervised anomaly detection for behavioral analysis |
| **Database** | PostgreSQL | Production-grade relational database for both Bank and SIEM |
| **SIEM Database Fallback** | SQLite | Automatic fallback if PostgreSQL is unavailable (development) |
| **Background Tasks** | Python threading | Non-blocking background threads for event collection and SIEM push |

---

# 5. Project Folder Structure

```
VaultX/
├── README.md
│
├── bank/
│   ├── README.md
│   ├── frontend/                    # React SPA (http://localhost:5173)
│   │   ├── package.json             # Dependencies: React, Vite, Tailwind, Axios, Lucide
│   │   ├── vite.config.js           # Vite config with API proxy to backend:5000
│   │   ├── tailwind.config.js       # Tailwind theme with dark mode support
│   │   ├── postcss.config.js        # PostCSS config for Tailwind
│   │   ├── index.html               # HTML entry point
│   │   └── src/
│   │       ├── main.jsx             # React entry: renders App with ThemeProvider + AuthProvider
│   │       ├── App.jsx              # Router: public routes + authenticated layout with Sidebar
│   │       ├── index.css            # Global styles, animations, dark mode utilities
│   │       ├── context/
│   │       │   ├── AuthContext.jsx   # Authentication state (token, user, login, logout)
│   │       │   └── ThemeContext.jsx  # Dark/light theme state (localStorage persistence)
│   │       ├── services/
│   │       │   └── api.js           # Axios instance + all API functions (auth, user, admin, transfer)
│   │       ├── components/
│   │       │   ├── Sidebar.jsx      # Navigation sidebar (desktop persistent, mobile drawer)
│   │       │   ├── Navbar.jsx       # Top bar with theme toggle, user menu, notifications
│   │       │   ├── Alert.jsx        # Reusable alert/error banner
│   │       │   ├── LoadingSpinner.jsx # Loading states and skeleton loaders
│   │       │   └── ProtectedRoute.jsx # Route guard requiring authentication
│   │       └── pages/
│   │           ├── LandingPage.jsx      # Public marketing page
│   │           ├── LoginPage.jsx        # User login form
│   │           ├── RegisterPage.jsx     # User registration form
│   │           ├── DashboardPage.jsx    # Balance card, quick actions, recent transactions
│   │           ├── TransferPage.jsx     # Money transfer form with validation
│   │           ├── TransactionsPage.jsx # Transaction history with filters
│   │           ├── ProfilePage.jsx      # User profile and account info
│   │           ├── AdminLoginPage.jsx   # Admin-specific login
│   │           ├── AdminDashboardPage.jsx # Admin dashboard with stats
│   │           ├── AdminUsersPage.jsx   # User management
│   │           └── AdminSecurityPage.jsx # Security events view
│   │
│   └── backend/                     # Flask REST API (http://localhost:5000)
│       ├── .env                     # Environment variables (not committed)
│       ├── .env.example             # Template for environment variables
│       ├── requirements.txt         # Python dependencies
│       ├── run.py                   # Entry point: creates app, runs on port 5000
│       ├── seed.py                  # Demo data seeder (creates users, accounts, transactions)
│       ├── config/
│       │   └── config.py            # Config classes (dev/prod) with DB URL, JWT keys, SIEM settings
│       └── app/
│           ├── __init__.py
│           ├── app.py               # Flask app factory: CORS, blueprints, tables, middleware
│           ├── auth/
│           │   └── __init__.py      # Auth utilities: hash_password, verify_password, create_token, token_required, admin_required
│           ├── models/
│           │   └── __init__.py      # SQLAlchemy models: User, Account, Transaction, LoginAttempt, SecurityEvent, AuditLog
│           ├── routes/
│           │   ├── auth.py          # POST /api/auth/register, POST /api/auth/login, POST /api/auth/logout
│           │   ├── user.py          # GET/PUT /api/user/profile, POST /api/user/change-password, GET /api/user/transactions
│           │   ├── transactions.py  # POST /api/transactions/transfer
│           │   ├── admin.py         # GET/POST /api/admin/* (users, transactions, security-events, stats)
│           │   └── security_events.py # GET /api/security-events (public, for SIEM consumption)
│           ├── services/
│           │   └── account_service.py # generate_account_number, create_account_for_user, process_transfer
│           └── logging/
│               └── security_logger.py # log_security_event (DB + SIEM push), log_audit
│
└── siem/
    ├── frontend/                    # React SPA (http://localhost:5174)
    │   ├── package.json             # Dependencies: React, Vite, Recharts, Socket.IO Client, Lucide
    │   ├── vite.config.js
    │   ├── postcss.config.js        # PostCSS config for Tailwind
    │   └── src/
    │       ├── main.jsx
    │       ├── App.jsx              # Routes: Login + protected layout (Sidebar + Navbar)
    │       ├── context/
    │       │   └── AuthContext.jsx   # SIEM auth state with role-based access
    │       ├── services/
    │       │   ├── api.js           # Axios instance for SIEM API
    │       │   └── socket.js        # Socket.IO client connection to SIEM backend
    │       ├── components/
    │       │   ├── Navbar.jsx       # Top bar with real-time monitor indicator
    │       │   ├── Sidebar.jsx      # Navigation with system health status
    │       │   ├── MetricCard.jsx   # Dashboard metric cards
    │       │   ├── SeverityBadge.jsx # Color-coded severity badges
    │       │   ├── MitreBadge.jsx   # MITRE ATT&CK technique badges
    │       │   └── RiskScoreGauge.jsx # Visual risk score gauge with factor breakdown
    │       └── pages/
    │           ├── LoginPage.jsx          # SOC analyst login
    │           ├── DashboardPage.jsx      # SOC dashboard with real-time charts
    │           ├── EventsPage.jsx         # Security events list
    │           ├── AlertsPage.jsx         # Alerts list with filters
    │           ├── AlertDetailPage.jsx     # Single alert with MITRE, IP intel, recommendations
    │           ├── IncidentsPage.jsx       # Incidents list
    │           ├── IncidentDetailPage.jsx  # Single incident with correlated alerts
    │           ├── TimelinePage.jsx        # Attack timeline visualization
    │           ├── MitrePage.jsx           # MITRE ATT&CK techniques database
    │           ├── IPIntelligencePage.jsx  # IP geolocation and reputation lookup
    │           ├── AnalyticsPage.jsx       # ML anomaly analytics
    │           ├── ReportsPage.jsx         # Report generation
    │           ├── SettingsPage.jsx        # System settings (thresholds)
    │           └── UsersPage.jsx           # SOC user management (admin only)
    │
    ├── tests/
    │   └── test_siem.py             # SIEM integration tests
    └── backend/                     # Flask + SocketIO (http://localhost:5001)
        ├── .env
        ├── .env.example
        ├── requirements.txt
        ├── run.py                   # Entry point: creates app, runs SocketIO on port 5001
        ├── clear_demo_data.py       # Database cleanup script for demo data
        └── app/
            ├── __init__.py          # App factory: DB, CORS, seed SOC users, start collector
            ├── config.py            # Config: DB URL, SIEM API key, collector settings
            ├── database.py          # db, bcrypt, socketio singleton instances
            ├── models/
            │   ├── user.py          # SOC user (Admin, Security Analyst, Viewer roles)
            │   ├── security_event.py # Ingested security events
            │   ├── alert.py         # Detection-generated alerts
            │   ├── incident.py      # Correlated incidents (groups of alerts)
            │   ├── ml_anomaly.py    # ML anomaly detection results
            │   ├── ip_intelligence.py # Cached IP geolocation data
            │   ├── mitre_technique.py # MITRE ATT&CK reference data
            │   ├── notification.py  # Notification delivery records
            │   ├── audit_log.py     # SOC audit trail
            │   └── setting.py       # Configurable system settings
            ├── routes/
            │   ├── auth_routes.py      # POST /api/auth/login, GET /api/auth/me
            │   ├── event_routes.py     # POST /api/events (ingestion), GET /api/events (query)
            │   ├── alert_routes.py     # GET/POST /api/alerts/* (list, detail, status, assign)
            │   ├── incident_routes.py  # GET /api/incidents/*
            │   ├── analytics_routes.py # GET /api/analytics/dashboard, GET /api/analytics/ml
            │   ├── mitre_routes.py     # GET /api/mitre/*
            │   ├── ip_routes.py        # GET /api/ip-intelligence/*
            │   ├── report_routes.py    # GET/POST /api/reports/*
            │   ├── settings_routes.py  # GET/PUT /api/settings/*
            │   └── user_routes.py      # GET/POST /api/users/*
            ├── collectors/
            │   └── securebank_collector.py # Background polling + full processing pipeline
            ├── detection/
            │   ├── rules.py         # 5 detection rules with configurable thresholds
            │   └── risk_engine.py   # Transparent composite risk scoring (0-100)
            ├── ml/
            │   └── anomaly_detector.py # Isolation Forest anomaly detection
            ├── services/
            │   ├── auth_service.py   # JWT generation, token_required decorator, role-based access
            │   ├── incident_service.py # Alert→Incident correlation, timeline builder
            │   ├── ip_service.py     # IP geolocation (ip-api.com) with caching
            │   ├── audit_service.py  # Audit trail logging
            │   └── report_generator.py # PDF/JSON report generation
            ├── notifications/
            │   └── dispatcher.py    # Discord/Slack webhook notifications for HIGH/CRITICAL alerts
            └── mitre/
                └── mitre_mapping.py # MITRE ATT&CK technique database and lookup
```

---

# 6. Bank Application

## Frontend (React + Vite)

The Bank frontend is a single-page application with two layouts:

1. **Public Layout**: Landing page, login, register — shown without authentication
2. **Authenticated Layout**: Sidebar + top navbar + page content — shown after login

### Pages

| Page | Route | Purpose | API Calls |
|------|-------|---------|-----------|
| Landing | `/` | Marketing page with feature overview | None |
| Login | `/login` | User authentication | `POST /api/auth/login` |
| Register | `/register` | New account creation | `POST /api/auth/register` |
| Dashboard | `/dashboard` | Balance, quick actions, recent transactions | `GET /api/user/profile`, `GET /api/user/transactions` |
| Transfer | `/transfer` | Send money to another account | `POST /api/transactions/transfer` |
| Transactions | `/transactions` | Full transaction history with filters | `GET /api/user/transactions` |
| Profile | `/profile` | User info, account details, security | `GET /api/user/profile`, `PUT /api/user/profile` |
| Admin Login | `/admin/login` | Admin authentication | `POST /api/admin/login` |
| Admin Dashboard | `/admin/dashboard` | System-wide statistics | `GET /api/admin/stats` |
| Admin Users | `/admin/users` | User management | `GET /api/admin/users`, `POST /api/admin/users/:id/toggle-status` |
| Admin Security | `/admin/security` | Security events view | `GET /api/admin/security-events` |

### State Management

- **AuthContext**: Stores `user` object and `token` in React state + `localStorage`
- **ThemeContext**: Stores dark/light theme preference in `localStorage`
- **Local component state**: Forms, loading states, error messages use `useState`

### API Communication

The `services/api.js` file creates an Axios instance with:
- **Base URL**: `/api` (proxied by Vite to `http://localhost:5000/api` in development)
- **Request interceptor**: Attaches `Authorization: Bearer <token>` header to every request
- **Response interceptor**: On 401 response, clears token and redirects to login

### Routing

React Router v6 with a nested layout pattern:
- Public routes render directly
- Protected routes are wrapped in `ProtectedLayout` which checks `useAuth().user`
- If not authenticated, redirects to `/login`
- The layout renders `Sidebar` + `Navbar` + `<Outlet />` (child route)

## Backend (Flask)

### Application Factory

`app/app.py` creates the Flask app:

1. Loads configuration from `config/config.py`
2. Initializes SQLAlchemy, CORS
3. Registers 5 blueprints: `auth_bp`, `user_bp`, `transactions_bp`, `admin_bp`, `security_events_bp`
4. Adds a `before_request` middleware that logs suspicious URL patterns (SQL injection, XSS)
5. Creates database tables with `db.create_all()`

### Routes

**Authentication (`/api/auth`)**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/register` | Create new user + account | No |
| POST | `/login` | Authenticate, get JWT | No |
| POST | `/logout` | Log security event | Yes |

**User (`/api/user`)**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/profile` | Get user + account data | Yes |
| PUT | `/profile` | Update first/last name | Yes |
| POST | `/change-password` | Change password | Yes |
| GET | `/transactions` | Paginated transaction history | Yes |
| GET | `/login-history` | Paginated login attempts | Yes |

**Transactions (`/api/transactions`)**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/transfer` | Send money to another account | Yes |

**Admin (`/api/admin`)**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/login` | Admin authentication | No |
| GET | `/users` | List all users | Admin |
| POST | `/users/:id/toggle-status` | Enable/disable user | Admin |
| GET | `/transactions` | All transactions | Admin |
| GET | `/security-events` | Security events | Admin |
| GET | `/login-activity` | Login attempts | Admin |
| GET | `/stats` | System statistics | Admin |

**Security Events (`/api/security-events`)**

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `""` | Query events (for SIEM) | No (public) |

---

# 7. Bank Database

## Tables (vaultx_bank)

### users

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| username | VARCHAR(80) | Unique, indexed |
| email | VARCHAR(120) | Unique, indexed |
| password_hash | VARCHAR(256) | bcrypt hash |
| first_name | VARCHAR(80) | |
| last_name | VARCHAR(80) | |
| role | VARCHAR(20) | "user" or "admin" |
| is_active | BOOLEAN | Default true |
| is_locked | BOOLEAN | Default false |
| failed_login_attempts | INTEGER | Default 0 |
| last_failed_login | TIMESTAMP | |
| lockout_until | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### accounts

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK → users.id, unique (1:1) |
| account_number | VARCHAR(20) | Unique, indexed, format: VB + 10 digits |
| balance | NUMERIC(12,2) | Default 0.00 |
| currency | VARCHAR(3) | Default "USD" |
| account_type | VARCHAR(20) | Default "checking" |
| status | VARCHAR(20) | "active" |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### transactions

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK → users.id, indexed |
| account_id | VARCHAR(36) | FK → accounts.id |
| transaction_type | VARCHAR(20) | "transfer_in", "transfer_out", "deposit", "withdrawal" |
| amount | NUMERIC(12,2) | |
| currency | VARCHAR(3) | Default "USD" |
| status | VARCHAR(20) | "pending", "completed", "failed" |
| description | TEXT | |
| recipient_account | VARCHAR(20) | |
| recipient_name | VARCHAR(160) | |
| reference | VARCHAR(50) | Format: TXF-XXXXXXXX |
| created_at | TIMESTAMP | |

### login_attempts

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK → users.id, nullable |
| username | VARCHAR(80) | |
| email | VARCHAR(120) | |
| success | BOOLEAN | |
| source_ip | VARCHAR(45) | |
| user_agent | TEXT | |
| failure_reason | VARCHAR(100) | "invalid_credentials" or "user_not_found" |
| created_at | TIMESTAMP | |

### security_events

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| event_id | VARCHAR(36) | Unique, indexed |
| timestamp | TIMESTAMP | Indexed |
| event_type | VARCHAR(50) | Indexed (LOGIN_SUCCESS, LOGIN_FAILED, etc.) |
| user_id | VARCHAR(36) | FK → users.id |
| username | VARCHAR(80) | |
| source_ip | VARCHAR(45) | Indexed |
| user_agent | TEXT | |
| endpoint | VARCHAR(255) | |
| http_method | VARCHAR(10) | |
| status | VARCHAR(20) | "SUCCESS", "FAILED", "BLOCKED" |
| metadata_json | JSON | Event-specific metadata |

### audit_logs

| Column | Type | Notes |
|--------|------|-------|
| id | VARCHAR(36) | Primary key (UUID) |
| user_id | VARCHAR(36) | FK → users.id |
| action | VARCHAR(50) | "CREATE", "UPDATE", "LOGOUT" |
| resource_type | VARCHAR(50) | "user", "transaction" |
| resource_id | VARCHAR(36) | |
| details | JSON | |
| source_ip | VARCHAR(45) | |
| created_at | TIMESTAMP | |

## ER Diagram

```
users (1) ──────── (1) accounts
  │
  ├── (1:N) transactions
  │
  ├── (1:N) login_attempts
  │
  ├── (1:N) security_events
  │
  └── (1:N) audit_logs
```

Each user has exactly one account. A user can have many transactions, login attempts, security events, and audit logs.

---

# 8. Authentication Flow

## Login Flow (Step by Step)

```
User enters credentials in React form
        │
        ▼
React: POST /api/auth/login { username, password }
        │
        ▼
Vite proxy forwards to Flask on port 5000
        │
        ▼
Flask auth.py: login() route
        │
        ├─ 1. Find user by username or email
        │
        ├─ 2. Check if account is locked (is_locked + lockout_until)
        │     └─ If locked: return 423 "Account is locked"
        │     └─ If lockout expired: unlock account
        │
        ├─ 3. Verify password with bcrypt.checkpw()
        │     └─ bcrypt automatically includes the salt in the hash
        │     └─ If wrong: increment failed_login_attempts
        │     └─ If attempts >= 5: lock account for 15 minutes
        │
        ├─ 4. On success: reset failed_login_attempts to 0
        │
        ├─ 5. Create LoginAttempt record (success=True)
        │
        ├─ 6. Create SecurityEvent (LOGIN_SUCCESS)
        │     └─ This event is simultaneously saved to DB
        │     └─ AND pushed to SIEM via background thread
        │
        ├─ 7. Generate JWT token with user_id, role, 1-hour expiry
        │
        └─ 8. Return { token, user } to frontend
                │
                ▼
        React: store token + user in localStorage
        React: set user state in AuthContext
        React: redirect to /dashboard
```

## Password Storage

Passwords are never stored in plain text. The Bank uses **bcrypt**:

```python
# Hashing (during registration)
salt = bcrypt.gensalt()          # Generate random salt
hash = bcrypt.hashpw(password, salt)  # Hash password with salt

# Verification (during login)
bcrypt.checkpw(password, password_hash)  # Returns True/False
```

bcrypt automatically embeds the salt in the hash, so you only need to store one string per user.

## JWT (JSON Web Token)

A JWT is a signed token containing user identity information:

```json
{
  "user_id": "uuid-here",
  "role": "user",
  "iat": "2026-08-22T10:00:00Z",
  "exp": "2026-08-22T11:00:00Z"
}
```

- **Signed** with `HS256` algorithm using the `JWT_SECRET_KEY`
- **Expires** after 1 hour (Bank) or 24 hours (SIEM)
- **Sent** in the `Authorization: Bearer <token>` header on every request
- **Verified** by the `@token_required` decorator before accessing protected routes

## Account Lockout

The Bank implements brute-force protection:
- After **5 failed login attempts**, the account is locked
- Lockout duration: **15 minutes**
- The user sees "Account is locked. Try again in X minutes."
- A `ACCOUNT_LOCKED` security event is generated (which the SIEM receives)

---

# 9. Transaction Flow

## Transfer Money (Step by Step)

```
User enters recipient account, amount, description in React form
        │
        ▼
React: POST /api/transactions/transfer
       { recipient_account, amount, description }
        │
        ▼
Flask transactions.py: create_transfer() route
        │
        ├─ 1. Validate required fields (recipient_account, amount)
        │
        ├─ 2. Validate amount > 0 and <= $100,000
        │
        ├─ 3. Call process_transfer() service
        │     │
        │     ├─ Find user's account (Account.query.filter_by)
        │     ├─ Check account is active
        │     ├─ Check sufficient balance
        │     │   └─ If insufficient: create failed transaction, raise ValueError
        │     ├─ Create Transaction record (type=transfer_out, status=completed)
        │     ├─ Deduct amount from balance
        │     └─ Save to database
        │
        ├─ 4. Create SecurityEvent (TRANSFER_SUCCESS)
        │     └─ Metadata includes: transaction_id, amount, recipient, reference
        │     └─ Pushed to SIEM in background thread
        │
        ├─ 5. Create AuditLog (CREATE, resource_type=transaction)
        │
        └─ 6. Return { transaction } to frontend
                │
                ▼
        React: show success state
        React: redirect to dashboard or transactions page
```

## Security Events Generated During Transfer

| Event Type | When | Status |
|------------|------|--------|
| `TRANSFER_CREATED` | Transfer succeeds | SUCCESS |
| `TRANSFER_FAILED` | Transfer fails (insufficient funds, error) | FAILED |
| `SUSPICIOUS_REQUEST` | SQL injection/XSS pattern detected in URL | BLOCKED |

---

# 10. Security Event System

## What is a Security Event?

A security event is a structured record of any security-relevant activity in the system.
Every login attempt, transfer, password change, or suspicious request generates a security event.

## Event Types Generated by VaultX Bank

| Event Type | Trigger | Metadata |
|------------|---------|----------|
| `LOGIN_SUCCESS` | User logs in with correct password | source_ip |
| `LOGIN_FAILED` | Wrong password or username | failure_reason ("invalid_credentials" or "user_not_found") |
| `ACCOUNT_LOCKED` | 5+ failed login attempts | reason, attempts count |
| `LOGOUT` | User logs out | — |
| `ACCOUNT_CREATED` | New user registers | email |
| `TRANSFER_CREATED` | Money transfer succeeds | transaction_id, amount, recipient_account, reference |
| `TRANSFER_FAILED` | Money transfer fails | amount, recipient_account, reason |
| `PASSWORD_CHANGE` | User changes password successfully | — |
| `PASSWORD_CHANGE_FAILED` | Wrong current password during change | reason |
| `ADMIN_LOGIN` | Admin logs in successfully | source_ip |
| `ADMIN_LOGIN_FAILED` | Wrong admin credentials | reason |
| `UNAUTHORIZED_ACCESS` | Non-admin tries admin endpoint | attempted_resource |
| `SUSPICIOUS_REQUEST` | SQL injection/XSS pattern in URL | pattern, path, query |

## How Events Are Created

Every event is created by the centralized `log_security_event()` function in `security_logger.py`:

```python
def log_security_event(event_type, status, user_id=None, ...):
    # 1. Create SecurityEvent record in Bank database
    event = SecurityEvent(...)
    db.session.add(event)
    db.session.commit()

    # 2. Push to SIEM in a background thread (non-blocking)
    thread = threading.Thread(
        target=_send_event_to_siem,
        args=(event_data,),
        daemon=True
    )
    thread.start()
```

This design means:
- The event is saved to the Bank's database immediately
- The SIEM push happens asynchronously, so it never blocks the user's request
- If the SIEM is offline, the Bank still works (the push silently fails)
- The SIEM collector also polls for events as a backup mechanism

---

# 11. Bank → SIEM Communication

## Two Mechanisms

VaultX uses **two complementary mechanisms** to get events from Bank to SIEM:

### Mechanism 1: Bank Pushes to SIEM (Real-time)

```
Bank Backend
    │
    │  Background thread: HTTP POST
    │  URL: http://localhost:5001/api/events
    │  Header: X-API-Key: vaultx_siem_api_key_2026
    │  Body: { event_id, source_app, event_type, status, username, ... }
    │
    ▼
SIEM Backend (POST /api/events)
    │
    ├─ Validate API key
    │
    └─ Process through full pipeline (normalize → detect → alert)
```

### Mechanism 2: SIEM Polls the Bank (Every 10 seconds)

```
SIEM Background Collector
    │
    │  Every 10 seconds: HTTP GET
    │  URL: http://localhost:5000/api/security-events
    │  Params: start_time=<last_checkpoint>, per_page=100
    │
    ▼
Bank Backend (GET /api/security-events)
    │
    │  Returns events newer than the checkpoint
    │
    ▼
SIEM Collector
    │
    ├─ Deduplicate (skip events already in SIEM DB)
    │
    └─ Process new events through full pipeline
```

## Why Two Mechanisms?

- **Push** provides near-real-time delivery (events appear within seconds)
- **Poll** provides reliability — if the push fails or the SIEM restarts, it can catch up
- The **checkpoint** (stored in the `settings` table as `last_event_timestamp`) ensures the SIEM never re-processes old events

## Event Processing Pipeline in SIEM

When an event arrives (via either mechanism), the SIEM processes it through:

```
Raw Event
    │
    ├─ 1. Deduplication (skip if external_id exists)
    │
    ├─ 2. Normalize (LOGIN_FAILED → login_failed, SUCCESS → success)
    │
    ├─ 3. Save to SIEM database
    │
    ├─ 4. Emit Socket.IO 'new_event' to browsers
    │
    ├─ 5. IP Intelligence lookup (ip-api.com, cached 7 days)
    │
    ├─ 6. ML Anomaly Detection (Isolation Forest)
    │
    ├─ 7. Detection Rule Engine (5 basic rules)
    │
    ├─ 8. Correlation Engine (6 advanced rules with cooldown)
    │     └─ If triggered: create Alert record
    │
    ├─ 9. Risk Score Calculation (0-100 composite score)
    │
    ├─ 10. Incident Correlation (group alerts by IP/user into incidents)
    │
    ├─ 11. Alert Cooldown (prevent duplicate alerts within cooldown window)
    │
    ├─ 12. Emit Socket.IO 'new_alert' and 'new_anomaly' to browsers
    │
    └─ 13. Notification Dispatch (Discord/Slack for HIGH/CRITICAL)
```

---

# 12. SIEM Application

## What is a SIEM?

**SIEM** stands for **Security Information and Event Management**. It is a system that:

1. **Collects** security data from multiple sources
2. **Normalizes** the data into a common format
3. **Correlates** events to find patterns
4. **Detects** threats using rules and machine learning
5. **Alerts** security analysts when something suspicious happens
6. **Provides** dashboards, reports, and investigation tools

In a real enterprise, a SIEM might monitor firewalls, servers, applications, and
network devices. VaultX's SIEM monitors one application (the Bank).

## SentinelSIEM Features

### Pages

| Page | Purpose |
|------|---------|
| SOC Dashboard | Real-time metrics, charts, live alert stream |
| Security Events | Searchable list of all ingested events |
| Alerts | List of detection-generated alerts with severity/status |
| Alert Detail | Single alert with MITRE mapping, IP intel, recommendations |
| Incidents | Grouped alerts representing correlated attack campaigns |
| Incident Detail | Single incident with its correlated alerts and events |
| Attack Timeline | Chronological visualization of an attack chain |
| MITRE ATT&CK | Reference database of attack techniques |
| IP Intelligence | IP geolocation and reputation lookup |
| Analytics & ML | ML anomaly detection results and statistics |
| Reports Center | Generate and download security reports (PDF, CSV, JSON) |
| System Settings | Configurable detection thresholds and correlation rules |
| User Management | Manage SOC analyst accounts (admin only) |

### Event vs Alert vs Incident

| Concept | Definition | Example |
|---------|-----------|---------|
| **Event** | A raw security observation | "User X logged in from IP Y at time T" |
| **Alert** | A detection rule was triggered | "5 failed logins from IP Y in 5 minutes = Possible Brute Force" |
| **Incident** | A group of related alerts | "Brute Force + Account Compromise from same IP = Campaign" |

---

# 13. SIEM Database

## Tables (vaultx_siem)

### security_events

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| external_id | VARCHAR(128) | Unique, indexed — dedup key |
| source_app | VARCHAR(64) | "VaultX Bank" |
| event_type | VARCHAR(64) | Indexed, normalized: login_success, login_failed, etc. |
| status | VARCHAR(32) | success, failed, blocked, denied |
| username | VARCHAR(80) | Indexed |
| source_ip | VARCHAR(45) | Indexed |
| destination_ip | VARCHAR(45) | |
| timestamp | DATETIME | Indexed |
| details | JSON | Event metadata |
| raw_data | TEXT | Original event JSON |
| normalized_at | DATETIME | |
| processed | BOOLEAN | Default false |

### alerts

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| title | VARCHAR(150) | e.g., "Possible Brute Force Attack" |
| description | TEXT | Detailed description |
| severity | VARCHAR(20) | LOW, MEDIUM, HIGH, CRITICAL |
| source_ip | VARCHAR(45) | Indexed |
| username | VARCHAR(80) | Indexed |
| timestamp | DATETIME | Indexed |
| mitre_technique_id | VARCHAR(30) | Indexed — e.g., "T1110" |
| evidence | JSON | List of correlated security events |
| status | VARCHAR(30) | NEW, INVESTIGATING, RESOLVED, FALSE_POSITIVE |
| risk_score | FLOAT | 0.0 to 100.0 |
| risk_factors | JSON | Breakdown of how score was calculated |
| assigned_to_id | INTEGER | FK → users.id |
| notes | JSON | Analyst notes |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### incidents

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| title | VARCHAR(180) | |
| description | TEXT | |
| severity | VARCHAR(20) | |
| status | VARCHAR(30) | OPEN, INVESTIGATING, RESOLVED, CLOSED |
| source_ip | VARCHAR(45) | Indexed |
| affected_user | VARCHAR(80) | Indexed |
| risk_score | FLOAT | Composite score |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### incident_events (junction table)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| incident_id | INTEGER | FK → incidents.id |
| alert_id | INTEGER | FK → alerts.id |
| security_event_id | INTEGER | FK → security_events.id |
| added_at | DATETIME | |

### ml_anomalies

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| event_id | INTEGER | FK → security_events.id |
| username | VARCHAR | |
| source_ip | VARCHAR | |
| anomaly_score | FLOAT | 0.0 to 1.0 |
| is_anomaly | BOOLEAN | |
| feature_vector | JSON | The 7 features used |
| reasoning | TEXT | Human-readable explanation |
| timestamp | DATETIME | |

### ip_intelligence

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| ip_address | VARCHAR(45) | Unique |
| country | VARCHAR | |
| country_code | VARCHAR | |
| region | VARCHAR | |
| city | VARCHAR | |
| isp | VARCHAR | |
| org | VARCHAR | |
| is_private | BOOLEAN | |
| is_malicious_flag | BOOLEAN | |
| raw_json | JSON | |
| updated_at | DATETIME | Cached for 7 days |

### Other tables

- **mitre_techniques** — Reference data for MITRE ATT&CK
- **users** — SOC analyst accounts (admin, analyst, viewer)
- **notifications** — Notification delivery records
- **audit_logs** — SOC audit trail
- **settings** — Configurable detection thresholds and system settings

## ER Diagram

```
security_events (1) ──── (N) incident_events (N) ──── (1) incidents
                                        │
alerts (1) ───────────── (N) ──────────┘

security_events (1) ──── (1) ml_anomalies

alerts (1) ──── (N) notifications

users (1) ──── (N) alerts (assigned_to)
users (1) ──── (N) audit_logs
```

---

# 14. SIEM Detection Engine

VaultX uses **two detection engines** that work together:

1. **Basic Detection Engine** (`detection/rules.py`) — 5 configurable rules for common attack patterns
2. **Advanced Correlation Engine** (`detection/correlation_engine.py`) — 6 correlation rules for sophisticated multi-event attack patterns

Both engines run on every incoming event. The correlation engine adds cooldown-based alert deduplication to prevent alert fatigue.

## Basic Detection Rules (5 Rules)

### Rule 1: Brute Force Attack (Repeated Failed Logins)

```text
Condition:  Status = "failed" AND
            Same source_ip has >= threshold (default: 5) failed events
            within time window (default: 5 minutes)
MITRE:      T1110 (Brute Force)
Severity:   HIGH (5-9 failures) or CRITICAL (10+ failures)
```

**Example**: 5 failed logins from 192.168.1.50 in 3 minutes → HIGH alert

## Rule 2: Account Compromise (Failed Logins → Success)

```text
Condition:  Status = "success" AND
            Same source_ip or username has >= 3 failed events
            within the past 15 minutes
MITRE:      T1078 (Valid Accounts)
Severity:   CRITICAL
```

**Example**: 3 wrong passwords followed by a correct one from the same IP → CRITICAL alert

## Rule 3: Privilege / Access Abuse (Unauthorized Admin Access)

```text
Condition:  Event type contains "admin" or "forbidden" OR status = "denied" AND
            Same source_ip has >= threshold (default: 3) such events
            within time window (default: 10 minutes)
MITRE:      T1068 (Exploitation for Privilege Escalation)
Severity:   HIGH
```

**Example**: 3 failed admin login attempts from same IP → HIGH alert

## Rule 4: Automated/Suspicious Activity (High Request Frequency)

```text
Condition:  Same source_ip has >= threshold (default: 20) events
            within time window (default: 1 minute)
MITRE:      T1499 (Endpoint Denial of Service)
Severity:   MEDIUM (20-39 events) or HIGH (40+ events)
```

**Example**: 25 requests from one IP in 1 minute → MEDIUM alert

## Rule 5: Unusual Login Source (New IP for User)

```text
Condition:  Login event (success or any login type) AND
            This username has never logged in from this source_ip before
MITRE:      T1078 (Valid Accounts)
Severity:   MEDIUM
```

**Example**: User "alice" logs in from a never-before-seen IP → MEDIUM alert

## Advanced Correlation Rules (6 Rules)

The correlation engine (`detection/correlation_engine.py`) detects sophisticated multi-event attack patterns that the basic rules might miss. Each rule has a **cooldown mechanism** to prevent duplicate alerts within the cooldown window.

### Correlation Rule 1: Brute Force (Same User/IP)

```text
Condition:  Status = "failed" AND
            Same source_ip AND same username has >= threshold failures
            within time window
MITRE:      T1110 (Brute Force)
Severity:   HIGH (5-9 failures) or CRITICAL (10+ failures)
```

### Correlation Rule 2: Password Spraying

```text
Condition:  Status = "failed" AND
            Same source_ip targets >= threshold distinct usernames
            within time window
MITRE:      T1110 (Brute Force)
Severity:   HIGH
Example:    5 different usernames targeted with failed logins from one IP
```

### Correlation Rule 3: Distributed Authentication Anomaly

```text
Condition:  Status = "failed" AND
            Total failures >= threshold AND
            Distinct source_ips >= threshold AND
            Distinct usernames >= threshold
            within broader time window (60 min)
MITRE:      T1110 (Brute Force)
Severity:   HIGH (4+ IPs, 4+ users) or MEDIUM
Example:    Coordinated distributed attack across multiple IPs and users
```

### Correlation Rule 4: Multi-Source Account Attack

```text
Condition:  Status = "failed" AND
            Same username targeted from >= threshold distinct source IPs
            within time window
MITRE:      T1110 (Brute Force)
Severity:   HIGH
Example:    One account targeted from 3+ different IP addresses
```

### Correlation Rule 5: Suspicious Auth Success After Failures

```text
Condition:  Status = "success" AND event is login-related AND
            >= threshold failures for same username OR same IP
            within time window
MITRE:      T1078 (Valid Accounts)
Severity:   HIGH (3-4 prior failures) or CRITICAL (5+ failures)
Example:    Successful login after 5 failed attempts suggests credential guessing
```

### Correlation Rule 6: Account Compromise (Failures → Success → Transfer)

```text
Condition:  Event is a transfer AND
            Same username had successful login preceded by >= threshold failures
            within broader time window (30 min)
MITRE:      T1078 (Valid Accounts)
Severity:   CRITICAL
Example:    Failed logins → successful login → money transfer = likely account compromise
```

### Alert Cooldown Mechanism

The correlation engine uses a cooldown mechanism to prevent duplicate alerts:
- Each correlation rule has a configurable cooldown window (default: 15 minutes)
- After an alert fires, the same pattern won't trigger again until the cooldown expires
- Cooldown timestamps are tracked in the `settings` table
- This prevents "alert fatigue" from repeated identical alerts

## Configurable Thresholds

All thresholds are stored in the `settings` table and can be modified via the SIEM Settings page:

### Basic Detection Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| brute_force_window_mins | 5 | Time window for brute force detection |
| brute_force_threshold | 5 | Min failed attempts to trigger |
| admin_abuse_window_mins | 10 | Time window for admin abuse detection |
| admin_abuse_threshold | 3 | Min denied attempts to trigger |
| high_freq_window_mins | 1 | Time window for high frequency detection |
| high_freq_threshold | 20 | Min events to trigger |

### Correlation Detection Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| password_spray_window_mins | 10 | Time window for password spraying detection |
| password_spray_user_threshold | 5 | Min distinct usernames to trigger |
| distributed_auth_window_mins | 60 | Time window for distributed auth detection |
| distributed_auth_threshold | 5 | Min total failures to trigger |
| distributed_auth_unique_ip_threshold | 3 | Min distinct source IPs |
| distributed_auth_unique_user_threshold | 3 | Min distinct usernames |
| multi_source_account_window_mins | 15 | Time window for multi-source attack detection |
| multi_source_account_threshold | 3 | Min distinct IPs targeting one account |
| suspicious_success_window_mins | 15 | Time window for failures before success |
| suspicious_success_fail_threshold | 3 | Min failures before success triggers alert |
| compromise_window_mins | 30 | Time window for account compromise detection |
| compromise_fail_threshold | 3 | Min failures before success+transfer triggers alert |

---

# 15. Alert Generation

## Risk Score Calculation

When an alert is triggered, a transparent composite risk score (0-100) is calculated:

| Factor | Max Points | Condition |
|--------|-----------|-----------|
| Base Severity | 35 | CRITICAL=35, HIGH=25, MEDIUM=15, LOW=5 |
| Event Volume | 20 | 10+ events=20, 5-9=12, 2-4=5 |
| Compromise Signal | 20 | Failed logins followed by success |
| New Login Source | 10 | IP never seen before for this user |
| IP Reputation | 15 | Known malicious IP (external lookup) |
| ML Anomaly Score | 20 | Isolation Forest anomaly score × 20 |

The final score determines the risk category:
- 85-100: CRITICAL
- 65-84: HIGH
- 35-64: MEDIUM
- 0-34: LOW

## Alert Lifecycle

```
Detection Rule triggers
        │
        ▼
Alert created (status = NEW)
        │
        ▼
SOC Analyst reviews → changes status to INVESTIGATING
        │
        ▼
After investigation → RESOLVED or FALSE_POSITIVE
```

---

# 16. ML Anomaly Detection

## How It Works

The SIEM uses **Isolation Forest** (from scikit-learn) for unsupervised anomaly detection.

### Feature Extraction

For each incoming event, 7 numerical features are extracted:

| Feature | Description | Range |
|---------|-------------|-------|
| login_hour | Hour of the day (0-23) | 0-23 |
| login_frequency_1h | Events from this user/IP in past hour | 0-N |
| failed_logins_1h | Failed logins in past hour | 0-N |
| success_logins_1h | Successful logins in past hour | 0-N |
| unique_ips_1h | Unique IPs for this user in past hour | 0-N |
| is_new_ip | 1 if this IP was never seen for this user, else 0 | 0 or 1 |
| request_freq_1m | Requests from this IP in past minute | 0-N |

### Anomaly Detection

1. The model is trained on historical events (or a synthetic baseline if fresh DB)
2. New events are scored: the model returns a decision function value
3. This is mapped to a 0.0-1.0 anomaly score
4. If score >= 0.70 or the model predicts -1, it's flagged as an anomaly
5. Human-readable reasoning is generated (e.g., "Elevated failed logins count (4/hr)")

### Training

- On first event, the model trains on the last 500 events from the database
- If fewer than 10 events exist, it uses a synthetic baseline of 10 normal behavior vectors
- The model is kept in memory (singleton) and retrained on each startup

---

# 17. Real-Time System (Socket.IO)

## How It Works

```
SIEM Backend processes new event
        │
        ├─ socketio.emit('new_event', event_data)
        │       │
        │       ▼
        │   All connected browsers receive the event instantly
        │
        ├─ socketio.emit('new_alert', alert_data)
        │       │
        │       ▼
        │   Dashboard updates metrics and alert table
        │
        ├─ socketio.emit('new_anomaly', anomaly_data)
        │       │
        │       ▼
        │   ML anomaly detected — live anomaly ticker updates
        │
        ├─ socketio.emit('alert_updated', alert_data)
        │       │
        │       ▼
        │   Alert status changed (INVESTIGATING, RESOLVED, etc.)
        │
        └─ socketio.emit('incident_updated', incident_data)
                │
                ▼
            Incident list updates
```

## Frontend Connection

```javascript
// socket.js
const socket = io('http://localhost:5001', {
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: 15,
    reconnectionDelay: 2000,
    transports: ['websocket', 'polling'],
});
```

The Dashboard subscribes to events:
```javascript
socket.on('new_alert', (alert) => {
    setRecentAlerts(prev => [alert, ...prev.slice(0, 9)]);
    setMetrics(prev => ({
        ...prev,
        total_alerts: prev.total_alerts + 1,
    }));
});

socket.on('new_event', () => {
    setMetrics(prev => ({ ...prev, total_events: prev.total_events + 1 }));
});
```

This means the dashboard updates in real-time without any page refresh.

---

# 18. API Documentation

## Bank API

### Authentication

```text
POST /api/auth/register
Body: { username, email, password, confirm_password, first_name, last_name }
Response: 201 { token, user }
Errors: 400 (missing fields), 409 (username/email taken)

POST /api/auth/login
Body: { username, password }
Response: 200 { token, user }
Errors: 401 (invalid credentials), 423 (account locked)

POST /api/auth/logout
Header: Authorization: Bearer <token>
Response: 200 { message }
```

### User

```text
GET /api/user/profile
Header: Authorization: Bearer <token>
Response: 200 { id, username, email, first_name, last_name, account: {...} }

PUT /api/user/profile
Header: Authorization: Bearer <token>
Body: { first_name, last_name }
Response: 200 { user }

POST /api/user/change-password
Header: Authorization: Bearer <token>
Body: { current_password, new_password }
Response: 200 { message }

GET /api/user/transactions?page=1&per_page=20
Header: Authorization: Bearer <token>
Response: 200 { transactions: [...], total, page, pages }
```

### Transactions

```text
POST /api/transactions/transfer
Header: Authorization: Bearer <token>
Body: { recipient_account, amount, description }
Response: 201 { transaction }
Errors: 400 (validation), 400 (insufficient funds)
```

### Security Events (Public — for SIEM)

```text
GET /api/security-events?page=1&per_page=100&start_time=<ISO>&event_type=<type>
Response: 200 { events: [...], total, page, pages }
```

## SIEM API

### Authentication

```text
POST /api/auth/login
Body: { username, password }
Response: 200 { token, user }

GET /api/auth/me
Header: Authorization: Bearer <token>
Response: 200 { user }
```

### Event Ingestion

```text
POST /api/events
Header: X-API-Key: vaultx_siem_api_key_2026
Body: { event_id, source_app, event_type, status, username, source_ip, timestamp, details }
Response: 200 { processed, errors }
```

### Events Query

```text
GET /api/events?page=1&per_page=20&event_type=<type>&source_ip=<ip>
Header: Authorization: Bearer <token>
Response: 200 { events: [...], total, page, pages }
```

### Alerts

```text
GET /api/alerts?page=1&severity=HIGH&status=NEW&detection_rule=BRUTE_FORCE
Header: Authorization: Bearer <token>
Response: 200 { alerts: [...], total, page, pages, per_page }

GET /api/alerts/<id>
Header: Authorization: Bearer <token>
Response: 200 { alert: {..., mitre_details, ip_intelligence, recommendations} }

PATCH /api/alerts/<id>/status
Header: Authorization: Bearer <token>
Body: { status: "INVESTIGATING" }
Response: 200 { alert }

POST /api/alerts/<id>/assign
Header: Authorization: Bearer <token>
Body: { user_id: <analyst_id> }
Response: 200 { alert }

POST /api/alerts/<id>/notes
Header: Authorization: Bearer <token>
Body: { text: "Analyst note" }
Response: 200 { alert }

GET /api/alerts/<id>/related-events
Header: Authorization: Bearer <token>
Response: 200 { events: [...], total, alert_id }

GET /api/alerts/detection-types
Header: Authorization: Bearer <token>
Response: 200 { detection_types: [{ rule, count }, ...] }
```

### Incidents

```text
GET /api/incidents?page=1&status=OPEN&severity=HIGH
Header: Authorization: Bearer <token>
Response: 200 { incidents: [...], total, page, pages }

GET /api/incidents/<id>
Header: Authorization: Bearer <token>
Response: 200 { incident: {..., events: [...], timeline: [...] } }

PATCH /api/incidents/<id>/status
Header: Authorization: Bearer <token>
Body: { status: "INVESTIGATING" }
Response: 200 { incident }

GET /api/incidents/timeline?incident_id=<id>
Header: Authorization: Bearer <token>
Response: 200 { timeline: [...] }
```

### Dashboard Analytics

```text
GET /api/analytics/dashboard
Header: Authorization: Bearer <token>
Response: 200 {
    metrics: { total_events, total_alerts, critical_alerts, high_alerts, open_incidents, total_anomalies },
    charts: {
        events_over_time, severity_distribution, top_source_ips,
        top_attack_types, mitre_distribution, geo_distribution
    },
    recent_alerts: [...]
}

GET /api/analytics/ml
Header: Authorization: Bearer <token>
Response: 200 {
    summary: { total_scanned, flagged_anomalies, anomaly_ratio },
    recent_anomalies: [...]
}
```

### Reports

```text
GET /api/reports/pdf
Header: Authorization: Bearer <token>
Response: 200 (PDF file download)

GET /api/reports/csv
Header: Authorization: Bearer <token>
Response: 200 (CSV file download)

GET /api/reports/json
Header: Authorization: Bearer <token>
Response: 200 (JSON file download)
```

### User Management (Admin Only)

```text
GET /api/users
Header: Authorization: Bearer <token>
Response: 200 { users: [...] }

POST /api/users
Header: Authorization: Bearer <token>
Body: { username, email, password, role }
Response: 201 { user }

PATCH /api/users/<id>/role
Header: Authorization: Bearer <token>
Body: { role: "Security Analyst" }
Response: 200 { user }
```

### Settings

```text
GET /api/settings
Header: Authorization: Bearer <token>
Response: 200 { settings: [{ key, value, description }, ...] }

PUT /api/settings
Header: Authorization: Bearer <token>
Body: { brute_force_threshold: "10", ... }
Response: 200 { message }
```

---

# 19. Environment Variables

## Bank Backend (.env)

```text
DATABASE_URL=postgresql://vaultx:vaultx@localhost:5432/vaultx_bank
SECRET_KEY=<random-secret-string>
JWT_SECRET_KEY=<another-random-secret>
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173
SIEM_API_URL=http://localhost:5001
SIEM_API_KEY=vaultx_siem_api_key_2026
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
RATE_LIMIT_PER_MINUTE=60
```

## SIEM Backend (.env)

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vaultx_siem
SQLITE_FALLBACK_URL=sqlite:///vaultx_siem.db
SECRET_KEY=<random-secret-string>
SIEM_API_KEY=vaultx_siem_api_key_2026
SECUREBANK_API_URL=http://localhost:5000/api/security-events
SECUREBANK_API_KEY=vaultx_siem_api_key_2026
SECUREBANK_POLL_INTERVAL=10
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
EMAIL_NOTIFICATIONS_ENABLED=false

# Correlation Engine Thresholds
BRUTE_FORCE_THRESHOLD=5
BRUTE_FORCE_WINDOW_MINUTES=5
PASSWORD_SPRAY_USER_THRESHOLD=5
PASSWORD_SPRAY_WINDOW_MINUTES=10
DISTRIBUTED_AUTH_THRESHOLD=5
DISTRIBUTED_AUTH_WINDOW_MINUTES=60
DISTRIBUTED_AUTH_UNIQUE_IP_THRESHOLD=3
DISTRIBUTED_AUTH_UNIQUE_USER_THRESHOLD=3
MULTI_SOURCE_ACCOUNT_THRESHOLD=3
MULTI_SOURCE_ACCOUNT_WINDOW_MINUTES=15
ALERT_DEDUP_WINDOW_MINUTES=15
```

---

# 20. Database Setup

## Prerequisites

- PostgreSQL 14+ installed and running
- pgAdmin or psql command-line tool

## Step 1: Create PostgreSQL User

```sql
CREATE USER vaultx WITH PASSWORD 'vaultx';
```

Or use the default `postgres` user if that's what your setup uses.

## Step 2: Create Databases

```sql
CREATE DATABASE vaultx_bank OWNER vaultx;
CREATE DATABASE vaultx_siem OWNER vaultx;
```

## Step 3: Tables

Tables are created automatically by SQLAlchemy's `db.create_all()` when each backend starts.
You do not need to run migrations manually.

## Step 4: Seed Data (Optional)

For the Bank, you can run the seed script to create demo users and transactions:

```powershell
cd bank\backend
python seed.py
```

This creates:
- 1 admin user (admin / Admin@123)
- 5 demo users (alice, bob, charlie, diana, eve)
- Sample transactions and login history for each

For the SIEM, default SOC users are created automatically on first startup:
- admin / admin123
- analyst / analyst123
- viewer / viewer123

MITRE ATT&CK techniques are also seeded automatically.

---

# 21. Installation Guide

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build tools |
| npm | 9+ | Package manager for frontend |
| PostgreSQL | 14+ | Database server |
| Git | Any | Version control (optional) |

## Step 1: Clone or Download

```powershell
cd "C:\Users\YourName\Documents"
# If using git:
git clone <repository-url> VaultX
# Or just extract the ZIP file
```

## Step 2: Create Databases

Open pgAdmin or psql and run:

```sql
CREATE USER vaultx WITH PASSWORD 'vaultx';
CREATE DATABASE vaultx_bank OWNER vaultx;
CREATE DATABASE vaultx_siem OWNER vaultx;
```

## Step 3: Setup Bank Backend

```powershell
cd "C:\path\to\VaultX\bank\backend"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env if needed (database URL, secrets)

# Seed demo data (optional)
python seed.py
```

## Step 4: Setup Bank Frontend

```powershell
cd "C:\path\to\VaultX\bank\frontend"

npm install
```

## Step 5: Setup SIEM Backend

```powershell
cd "C:\path\to\VaultX\siem\backend"

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
```

## Step 6: Setup SIEM Frontend

```powershell
cd "C:\path\to\VaultX\siem\frontend"

npm install
```

---

# 22. How to Run

Open **4 separate terminal windows** (PowerShell or Command Prompt):

### Terminal 1 — Bank Backend

```powershell
cd "C:\path\to\VaultX\bank\backend"
venv\Scripts\activate
python run.py
```

> **Running on http://localhost:5000**

### Terminal 2 — Bank Frontend

```powershell
cd "C:\path\to\VaultX\bank\frontend"
npm run dev
```

> **Running on http://localhost:5173**

### Terminal 3 — SIEM Backend

```powershell
cd "C:\path\to\VaultX\siem\backend"
venv\Scripts\activate
python run.py
```

> **Running on http://localhost:5001**

### Terminal 4 — SIEM Frontend

```powershell
cd "C:\path\to\VaultX\siem\frontend"
npm run dev
```

> **Running on http://localhost:5174**

### Verify All Services

| Service | URL | Expected |
|---------|-----|----------|
| Bank Frontend | http://localhost:5173 | Landing page loads |
| Bank API | http://localhost:5000/api/health | `{"status": "ok", "service": "bank-backend"}` |
| SIEM Frontend | http://localhost:5174 | Login page loads |
| SIEM API | http://localhost:5001/api/health | `{"status": "ok", "service": "siem-backend"}` |

---

# 23. End-to-End Examples

## Example 1: Brute Force Detection

```text
Step 1: Open Bank (http://localhost:5173)
Step 2: Try to login with wrong password 5 times

What happens internally:

Attempt 1:
  Bank Backend: verify_password() fails
  → LoginAttempt saved (success=False)
  → failed_login_attempts incremented to 1
  → SecurityEvent( LOGIN_FAILED ) saved to vaultx_bank
  → Pushed to SIEM via HTTP POST

Attempt 2-4: Same as above (counter reaches 4)

Attempt 5:
  Bank Backend: verify_password() fails
  → failed_login_attempts reaches 5 (MAX_LOGIN_ATTEMPTS)
  → Account locked (is_locked=True, lockout_until = now + 15 min)
  → SecurityEvent( ACCOUNT_LOCKED ) saved
  → User sees "Account locked due to too many failed attempts"

Meanwhile in SIEM:
  Event arrives → normalized to "login_failed"
  → Detection Rule 1 checks: 5 failed events from same IP in 5 min
  → THRESHOLD REACHED
  → Alert created: "Possible Brute Force Attack" (HIGH severity)
  → MITRE T1110 mapped
  → Risk Score calculated (e.g., 72/100)
  → Incident created (or added to existing)
  → Socket.IO emits 'new_alert' to dashboard
  → SOC analyst sees the alert appear in real-time
```

## Example 2: Successful Transfer

```text
Step 1: Login to Bank as "alice" (alice / Alice@123)
Step 2: Transfer $100 to account "VB1234567890"

What happens internally:

Bank Backend:
  1. Validate: amount > 0, amount <= $100,000
  2. Find alice's account, check balance >= $100
  3. Create Transaction (transfer_out, $100, completed)
  4. Deduct $100 from alice's balance
  5. SecurityEvent( TRANSFER_CREATED ) with metadata:
     { transaction_id, amount: 100, recipient_account: "VB1234567890" }
  6. Push event to SIEM

SIEM Backend:
  1. Receive event, deduplicate
  2. Normalize: TRANSFER_CREATED → fund_transfer
  3. Save to vaultx_siem
  4. Emit Socket.IO 'new_event'
  5. IP Intelligence lookup (127.0.0.1 → Private Network)
  6. ML Anomaly Detection (likely normal)
  7. Detection Rules: no rule matches fund_transfer
  8. No alert created (this is normal behavior)
```

## Example 3: New Login Source

```text
Step 1: Login to Bank as "alice" from a new IP (e.g., different machine)

What happens:

SIEM receives LOGIN_SUCCESS event from new IP
  → Detection Rule 5 checks: has alice ever logged in from this IP before?
  → No prior logins from this IP
  → Alert: "Unusual Login Source Detected" (MEDIUM severity)
  → MITRE T1078 mapped
  → SOC analyst sees the alert
```

---

# 24. Failure Scenarios

## Bank Database Unavailable

| What Happens | User Sees | How to Fix |
|--------------|-----------|------------|
| Bank backend cannot connect to PostgreSQL | 500 Internal Server Error | Start PostgreSQL, check DATABASE_URL in .env |
| Tables don't exist | SQLAlchemy error on query | Tables are auto-created on startup; ensure DB exists |

## SIEM Backend Unavailable

| What Happens | User Sees | How to Fix |
|--------------|-----------|------------|
| Bank cannot push events to SIEM | Bank works normally; no error to user | Start SIEM backend |
| SIEM collector cannot poll Bank | No new events in SIEM | Start Bank backend |
| Events still saved in Bank DB | Events available when SIEM comes back online | SIEM collector catches up on next poll |

**Key design point**: The Bank application is **never affected** by SIEM downtime. The SIEM push uses a background thread with a 5-second timeout. If it fails, it silently continues. The polling mechanism also provides a catch-up capability.

### Invalid JWT Token

| What Happens | User Sees |
|--------------|-----------|
| Token expired (>1h for Bank, >24h for SIEM) | Redirected to login page |
| Token tampered with | 401 "Invalid token" |
| No token provided | 401 "Authentication required" |

### Invalid Transaction

| Scenario | Error | Security Event |
|----------|-------|----------------|
| Insufficient balance | "Insufficient funds" (400) | `TRANSFER_FAILED` |
| Amount <= 0 | "Amount must be positive" (400) | None |
| Amount > $100,000 | "Transfer amount exceeds limit" (400) | None |
| Account not found | "Account not found" (400) | None |

### Frontend Cannot Reach Backend

| What Happens | How to Fix |
|--------------|------------|
| CORS error | Check CORS_ORIGINS in Bank .env matches frontend URL |
| Network error | Ensure backend is running on correct port |
| Vite proxy not working | Check vite.config.js proxy configuration |

---

# 25. Troubleshooting Guide

## Common Issues

### "Port 5000 already in use"

```powershell
# Find and kill the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### "PostgreSQL connection failed"

1. Ensure PostgreSQL service is running: `pg_isready`
2. Check DATABASE_URL in .env matches your PostgreSQL setup
3. Ensure the database `vaultx_bank` or `vaultx_siem` exists
4. Verify username/password are correct

### "Database does not exist"

```sql
CREATE DATABASE vaultx_bank;
CREATE DATABASE vaultx_siem;
```

### "ModuleNotFoundError"

```powershell
# Activate virtual environment first
venv\Scripts\activate
pip install -r requirements.txt
```

### "npm install failure"

```powershell
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules
npm install
```

### "CORS Error in Browser"

Check that the Bank backend's `CORS_ORIGINS` includes `http://localhost:5173` and the SIEM backend allows `http://localhost:5174`.

### "401 Unauthorized"

- Token may have expired — log in again
- Check that the `Authorization: Bearer <token>` header is being sent
- For SIEM event ingestion, check the `X-API-Key` header

### "SIEM Events Not Appearing"

1. Check SIEM backend is running: `curl http://localhost:5001/api/health`
2. Check Bank backend is running: `curl http://localhost:5000/api/health`
3. Check the SIEM API key matches in both .env files
4. Check the collector is running (look for "[SecureBank Collector] Background collector loop started." in SIEM logs)
5. Check the `settings` table for `last_event_timestamp` checkpoint

### "Socket.IO Not Updating"

1. Check the SIEM backend is running with Flask-SocketIO
2. Check browser console for Socket.IO connection messages
3. Ensure WebSocket transport is not blocked by firewall

---

# 26. Testing Guide

## Manual Testing Checklist

### Registration & Login

| Action | Expected Result | Where to Verify |
|--------|----------------|-----------------|
| Register with valid data | Account created, redirected to dashboard | Bank UI, Bank DB `users` table |
| Register with existing username | Error "Username already taken" | Bank UI |
| Register with mismatched passwords | Error "Passwords do not match" | Bank UI |
| Login with correct credentials | JWT token received, dashboard shown | Bank UI |
| Login with wrong password | Error "Invalid credentials" | Bank UI |
| Login 5 times with wrong password | Account locked for 15 minutes | Bank DB `users.is_locked` |
| Logout | Token cleared, redirected to login | Bank UI, Security event generated |

### Transactions

| Action | Expected Result | Where to Verify |
|--------|----------------|-----------------|
| Transfer money with sufficient balance | Transaction created, balance updated | Bank UI, Bank DB `transactions`, `accounts` |
| Transfer with insufficient balance | Error "Insufficient funds" | Bank UI |
| Transfer $0 or negative | Error "Amount must be positive" | Bank UI |
| Transfer > $100,000 | Error "Transfer amount exceeds limit" | Bank UI |
| View transaction history | List of transactions shown | Bank UI, Bank DB `transactions` |

### Security Events & SIEM

| Action | Expected Result | Where to Verify |
|--------|----------------|-----------------|
| Login successfully | `LOGIN_SUCCESS` event in Bank DB | Bank DB `security_events` |
| Login with wrong password | `LOGIN_FAILED` event in Bank DB | Bank DB `security_events` |
| 5 failed logins | `ACCOUNT_LOCKED` event + brute force alert | Bank DB + SIEM DB `alerts` |
| Transfer money | `TRANSFER_CREATED` event | Bank DB + SIEM DB `security_events` |
| View SIEM dashboard | Metrics match actual DB counts | SIEM UI dashboard |
| SIEM real-time updates | New alerts appear without refresh | SIEM UI (open two browser tabs) |

### SIEM Detection

| Action | Expected Result | Where to Verify |
|--------|----------------|-----------------|
| 5 failed logins from same IP | "Possible Brute Force Attack" alert (HIGH) | SIEM DB `alerts`, SIEM UI |
| Success after 3+ failures | "Possible Account Compromise" alert (CRITICAL) | SIEM DB `alerts` |
| Login from new IP | "Unusual Login Source" alert (MEDIUM) | SIEM DB `alerts` |

### Admin Features

| Action | Expected Result | Where to Verify |
|--------|----------------|-----------------|
| Admin login | Admin dashboard with stats | Bank UI admin panel |
| View all users | User list with account info | Bank UI admin panel |
| Toggle user status | User enabled/disabled | Bank DB `users.is_active` |

---

# 27. Security Concepts Used

## Authentication

- **Password Hashing (bcrypt)**: Passwords are never stored in plain text. bcrypt automatically includes a random salt in each hash.
- **JWT (JSON Web Tokens)**: Stateless authentication tokens that contain user identity and expiry. The server doesn't store sessions — it verifies the token on each request.
- **Token Expiry**: Bank tokens expire after 1 hour, SIEM tokens after 24 hours.

## Authorization

- **Role-Based Access Control (RBAC)**: Bank has "user" and "admin" roles. SIEM has "Admin", "Security Analyst", and "Viewer" roles.
- **Protected Routes**: The `@token_required` decorator ensures only authenticated users can access certain endpoints.
- **Admin Protection**: The `@admin_required` decorator ensures only admin-role users can access admin endpoints.

## Account Security

- **Account Lockout**: After 5 failed login attempts, the account is locked for 15 minutes.
- **Login Attempt Tracking**: Every login attempt (success or failure) is recorded with IP, user agent, and timestamp.

## Monitoring

- **Security Event Logging**: Every significant action generates a structured security event.
- **Audit Trail**: Every create/update action is logged in the audit_logs table.
- **Suspicious Request Detection**: The `before_request` middleware detects SQL injection and XSS patterns in URLs.

## Detection

- **Rule-Based Detection**: 5 basic configurable rules detect brute force, account compromise, privilege abuse, automated activity, and unusual login sources.
- **Advanced Correlation Detection**: 6 correlation rules detect sophisticated multi-event patterns: Password Spraying, Distributed Authentication Anomaly, Multi-Source Account Attack, Suspicious Auth Success After Failures, and Account Compromise chains.
- **Alert Cooldown**: Prevents duplicate alerts for the same pattern within configurable cooldown windows.
- **ML-Based Detection**: Isolation Forest anomaly detection identifies behavioral deviations.
- **Risk Scoring**: Transparent composite scoring (0-100) based on multiple threat factors.
- **MITRE ATT&CK Mapping**: Each alert is mapped to a MITRE ATT&CK technique for standardized threat classification.

## Event Pipeline

- **Push + Pull Architecture**: Bank pushes events to SIEM in real-time; SIEM polls as a reliability mechanism.
- **Non-Blocking Design**: SIEM push happens in a background thread, never blocking the Bank's user-facing requests.
- **Graceful Degradation**: If SIEM is offline, the Bank continues working normally.

---

# 28. Learning Roadmap

## Beginner (Start Here)

1. **React Basics**: Components, JSX, props, state (useState), effects (useEffect)
2. **Flask Basics**: Routes, request/response, JSON, Blueprints
3. **REST API**: HTTP methods (GET, POST, PUT, PATCH, DELETE), status codes, headers
4. **PostgreSQL**: CREATE TABLE, INSERT, SELECT, WHERE, JOIN, indexes
5. **SQLAlchemy**: Model definition, querying, relationships, sessions

## Intermediate

6. **JWT Authentication**: Token generation, verification, expiry, Bearer header
7. **bcrypt Password Hashing**: Salt, hash, verify
8. **React State Management**: Context API, custom hooks, localStorage persistence
9. **React Router**: Nested routes, route guards, navigation
10. **Axios Interceptors**: Request/response modification, global error handling
11. **Socket.IO**: Real-time bidirectional communication, events, rooms
12. **Database Relationships**: One-to-one (User:Account), one-to-many (User:Transaction)

## Cybersecurity

13. **SIEM Concepts**: Event collection, normalization, correlation, detection
14. **Security Events**: Structured logging, event types, metadata
15. **Detection Rules**: Threshold-based detection, time windows, configurable parameters
16. **Alert Management**: Severity, status lifecycle, assignment, investigation
17. **MITRE ATT&CK**: Tactics, techniques, mapping to real-world attack patterns
18. **Brute Force Detection**: Failed login thresholds, IP-based tracking
19. **Risk Scoring**: Multi-factor composite scoring, transparent reasoning
20. **IP Intelligence**: Geolocation, reputation, private vs public classification
21. **SOC Workflow**: Event → Alert → Investigation → Resolution

## Advanced

22. **ML Anomaly Detection**: Isolation Forest, feature engineering, behavioral baselines
23. **Incident Correlation**: Grouping related alerts into incidents
24. **Advanced Correlation Rules**: Multi-event pattern detection (Password Spraying, Distributed Auth, etc.)
25. **Alert Cooldown & Deduplication**: Preventing alert fatigue from repeated identical detections
26. **Event Pipeline Architecture**: Push vs pull, deduplication, normalization
27. **Background Processing**: Threading, non-blocking design, graceful degradation
28. **Distributed Systems**: Two independent applications communicating via HTTP
29. **Report Generation**: PDF/CSV/JSON export for SOC reporting
30. **Production Deployment**: Docker, reverse proxy (nginx), HTTPS, environment management
31. **Scaling**: Horizontal scaling, load balancing, database optimization

---

# 29. Interview Preparation

## 30-Second Explanation

> "VaultX is a cybersecurity project consisting of a simulated banking application
> and a SIEM (Security Information and Event Management) system. The Bank generates
> real security events for every user action — logins, transfers, password changes.
> These events are sent to the SIEM, which uses a detection engine with 11 rules
> (5 basic + 6 advanced correlation) and an ML anomaly detector to identify threats
> like brute force attacks, password spraying, distributed attacks, and account
> compromise. Alerts are generated in real-time and displayed on a SOC dashboard
> with MITRE ATT&CK mapping, risk scoring, and report generation."

## 1-Minute Explanation

> "VaultX demonstrates how a real Security Operations Center monitors a live
> application. It has two components: a Flask-based banking backend with React frontend,
> and a SIEM system with its own backend and dashboard.
>
> When a user logs in or transfers money, the bank creates a structured security event
> and pushes it to the SIEM. The SIEM processes every event through a pipeline:
> deduplication, normalization, IP intelligence lookup, ML anomaly detection, and a
> rule-based detection engine.
>
> The detection engine has 5 basic rules plus 6 advanced correlation rules covering
> brute force detection, account compromise detection, privilege abuse detection,
> high-frequency request detection, unusual login source detection, password spraying,
> distributed authentication anomalies, multi-source account attacks, suspicious auth
> success after failures, and full account compromise chains. When a rule triggers,
> an alert is created with a transparent risk score (0-100) based on severity, event
> volume, compromise signals, and ML anomaly scores.
>
> Alerts are automatically correlated into incidents. The dashboard updates in real-time
> using Socket.IO. Every alert is mapped to a MITRE ATT&CK technique for standardized
> threat classification."

## 3-Minute Technical Explanation

> "The architecture is a distributed event-driven system with two independent Flask
> applications communicating via REST APIs.
>
> **Bank Backend**: Flask with SQLAlchemy ORM, JWT authentication with bcrypt password
> hashing, role-based access control (user/admin), account lockout after 5 failed attempts.
> Every action generates a security event that's saved to PostgreSQL and simultaneously
> pushed to the SIEM via a background thread (non-blocking).
>
> **SIEM Backend**: Flask with Flask-SocketIO for real-time updates. It has a background
> collector that polls the Bank every 10 seconds as a reliability mechanism, in addition
> to receiving pushed events. Each event goes through a processing pipeline:
>
> First, deduplication using an external event ID. Then normalization — converting the
> Bank's UPPER_CASE event types to lowercase_snake format. The event is saved to the
> SIEM's PostgreSQL database and broadcast via Socket.IO.
>
> Next, IP intelligence lookup using ip-api.com with 7-day caching in the database.
> Then ML anomaly detection using scikit-learn's Isolation Forest — it extracts 7
> behavioral features (login hour, frequency, failed attempts, unique IPs, new IP flag,
> request rate) and scores the event for anomalous behavior.
>
> The detection engine evaluates 5 basic configurable rules plus 6 advanced correlation
> rules (with cooldown-based deduplication). When a rule triggers, a risk score is
> calculated as a transparent composite of 6 factors: severity, event volume, compromise
> signals, new login source, IP reputation, and ML anomaly score. The score ranges
> from 0-100 and determines the risk category.
>
> Alerts are correlated into incidents by matching source IP and affected user within
> a 4-hour window. The system also supports Discord and Slack webhook notifications
> for HIGH and CRITICAL alerts, plus PDF/CSV/JSON report generation.
>
> The frontend uses React with Tailwind CSS and Recharts for visualizations. Real-time
> updates use Socket.IO so the dashboard refreshes without page reloads."

## Architecture Explanation

> "The system follows a producer-consumer architecture:
> - **Producer**: Bank application generates security events
> - **Transport**: Dual mechanism — HTTP push (real-time) + polling (reliable)
> - **Consumer**: SIEM processes events through a multi-stage pipeline
> - **Output**: Alerts, incidents, risk scores, real-time dashboard updates
>
> The two databases are intentionally separate — the Bank's database is for banking
> operations, the SIEM's database is for security monitoring. They communicate only
> through the event API, maintaining clean separation of concerns."

## Security Explanation

> "Security is implemented at multiple layers:
> - **Authentication**: bcrypt password hashing + JWT tokens with expiry
> - **Authorization**: Role-based access control with decorator-based enforcement
> - **Account Protection**: Automatic lockout after 5 failed attempts
> - **Input Validation**: Server-side validation on all inputs
> - **Suspicious Request Detection**: Middleware checks for SQL injection and XSS patterns
> - **Audit Trail**: Every significant action is logged with IP and timestamp
> - **Event Monitoring**: All actions generate security events for SIEM analysis
> - **Detection Engine**: Rule-based + ML-based threat detection
> - **Incident Response**: Alert correlation and severity-based notification"

---

# 30. Code Explanation

## Security Event Logger (`bank/backend/app/logging/security_logger.py`)

```text
log_security_event()
    │
    ├─ Gets context from Flask request (IP, user agent, endpoint)
    │
    ├─ Creates SecurityEvent record → saves to Bank PostgreSQL
    │
    └─ Spawns background thread → _send_event_to_siem()
           │
           ├─ Gets SIEM_API_URL and SIEM_API_KEY from config
           │
           ├─ HTTP POST to SIEM /api/events with X-API-Key header
           │
           └─ Silently handles connection errors (SIEM offline = OK)
```

**Why background thread?** If the SIEM push fails or is slow, it doesn't delay
the user's login or transfer. The user gets their response immediately.

## SIEM Collector (`siem/backend/app/collectors/securebank_collector.py`)

```text
SecureBankCollector._run_loop()
    │
    ├─ Every 10 seconds (configurable):
    │
    ├─ poll_securebank_api()
    │     │
    │     ├─ GET Bank /api/security-events?start_time=<checkpoint>&per_page=100
    │     │
    │     ├─ For each event: process_raw_event()
    │     │     │
    │     │     ├─ Deduplication check (external_id unique constraint)
    │     │     ├─ Normalize event type and status
    │     │     ├─ Save to SIEM database
    │     │     ├─ Emit Socket.IO 'new_event'
    │     │     ├─ IP Intelligence lookup
    │     │     ├─ ML Anomaly Detection
    │     │     ├─ Detection Rule Engine (5 basic rules)
    │     │     ├─ Correlation Engine (6 advanced rules)
    │     │     │     └─ If triggered: create Alert
    │     │     ├─ Risk Score Calculation
    │     │     ├─ Alert Cooldown (prevent duplicate alerts)
    │     │     ├─ Incident Correlation
    │     │     └─ Emit Socket.IO 'new_alert' + 'new_anomaly'
    │     │
    │     └─ Update checkpoint timestamp
    │
    └─ Sleep for POLL_INTERVAL seconds
```

## Detection Rules (`siem/backend/app/detection/rules.py`)

```text
DetectionRuleEngine.evaluate_rules(event)
    │
    ├─ Rule 1: Brute Force
    │     Query: COUNT(failed events from same IP in window) >= threshold
    │
    ├─ Rule 2: Account Compromise
    │     Query: Event is success AND COUNT(failures from same IP/user in 15min) >= 3
    │
    ├─ Rule 3: Privilege Abuse
    │     Query: Event contains "admin"/"denied" AND COUNT(same in window) >= threshold
    │
    ├─ Rule 4: High Frequency
    │     Query: COUNT(all events from same IP in 1min) >= threshold
    │
    └─ Rule 5: New Login Source
          Query: Event is login AND COUNT(prior logins from this IP for this user) == 0
```

## Correlation Engine (`siem/backend/app/detection/correlation_engine.py`)

```text
CorrelationEngine.evaluate(event)
    │
    ├─ Rule 1: Brute Force (same user/IP)
    │     Query: COUNT(failures from same IP AND same user in window) >= threshold
    │     Cooldown: Prevents duplicate alerts within window_mins
    │
    ├─ Rule 2: Password Spraying (same IP, many users)
    │     Query: COUNT(DISTINCT usernames with failures from same IP) >= threshold
    │     Cooldown: Prevents duplicate alerts within window_mins
    │
    ├─ Rule 3: Distributed Auth Anomaly (many IPs, many users)
    │     Query: Total failures >= threshold AND distinct IPs >= threshold AND distinct users >= threshold
    │     Cooldown: Prevents duplicate alerts within window_mins
    │
    ├─ Rule 4: Multi-Source Account Attack (one user, many IPs)
    │     Query: COUNT(DISTINCT source_ips targeting same username) >= threshold
    │     Cooldown: Prevents duplicate alerts within window_mins
    │
    ├─ Rule 5: Suspicious Auth Success (failures → success)
    │     Query: Event is login success AND COUNT(failures for same user/IP in window) >= threshold
    │     Cooldown: Prevents duplicate alerts within window_mins
    │
    └─ Rule 6: Account Compromise (failures → success → transfer)
          Query: Event is transfer AND successful login preceded by failures for same user in window
          Cooldown: Prevents duplicate alerts within window_mins
```

## Risk Engine (`siem/backend/app/detection/risk_engine.py`)

```text
calculate_transparent_risk_score(alert_data, ml_anomaly_score, ip_info)
    │
    ├─ Base severity points (5-35 pts)
    ├─ Event volume factor (0-20 pts)
    ├─ Compromise signal bonus (0-20 pts)
    ├─ New login source bonus (0-10 pts)
    ├─ IP reputation factor (0-15 pts)
    ├─ ML anomaly score (0-20 pts)
    │
    └─ Total = min(100, sum of all factors)
         Risk category = CRITICAL (≥85) / HIGH (≥65) / MEDIUM (≥35) / LOW
```

---

# 31. Data Flow Diagrams

## Overall Architecture

```mermaid
graph TB
    subgraph Bank
        BF[Bank Frontend<br/>React + Vite :5173]
        BB[Bank Backend<br/>Flask :5000]
        BDB[(Bank PostgreSQL<br/>vaultx_bank)]
    end

    subgraph SIEM
        SF[SIEM Frontend<br/>React + Vite :5174]
        SB[SIEM Backend<br/>Flask + SocketIO :5001]
        SDB[(SIEM PostgreSQL<br/>vaultx_siem)]
    end

    BF -->|REST API| BB
    BB <-->|SQLAlchemy| BDB
    BB -->|HTTP POST + API Key| SB
    SB -->|HTTP GET + Polling| BB
    SB <-->|SQLAlchemy| SDB
    SB -->|Socket.IO WebSocket| SF
    SB -->|Detection Rules + ML + Correlation| SB
```

## Login Flow

```mermaid
sequenceDiagram
    participant U as User
    participant BF as Bank Frontend
    participant BB as Bank Backend
    participant BDB as Bank DB
    participant SIEM as SIEM Backend

    U->>BF: Enter credentials
    BF->>BB: POST /api/auth/login
    BB->>BDB: Query user by username
    BDB-->>BB: User record
    BB->>BB: bcrypt.checkpw(password, hash)
    
    alt Login Success
        BB->>BDB: Save LoginAttempt (success=True)
        BB->>BDB: Save SecurityEvent (LOGIN_SUCCESS)
        BB->>SIEM: POST /api/events (background thread)
        BB->>BB: Generate JWT token
        BB-->>BF: { token, user }
        BF->>BF: Store in localStorage
        BF-->>U: Dashboard page
    else Login Failed
        BB->>BDB: Save LoginAttempt (success=False)
        BB->>BDB: Increment failed_login_attempts
        BB->>BDB: Save SecurityEvent (LOGIN_FAILED)
        BB->>SIEM: POST /api/events (background thread)
        BB-->>BF: 401 "Invalid credentials"
        BF-->>U: Error message
    end
```

## Transaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant BF as Bank Frontend
    participant BB as Bank Backend
    participant BDB as Bank DB
    participant SIEM as SIEM Backend

    U->>BF: Enter transfer details
    BF->>BB: POST /api/transactions/transfer
    BB->>BDB: Query user account
    BB->>BB: Validate amount, check balance
    BB->>BDB: Create Transaction record
    BB->>BDB: Update account balance
    BB->>BDB: Save SecurityEvent (TRANSFER_CREATED)
    BB->>SIEM: POST /api/events (background thread)
    BB-->>BF: { transaction }
    BF-->>U: Success message
```

## Bank → SIEM Event Flow

```mermaid
sequenceDiagram
    participant BB as Bank Backend
    participant SIEM as SIEM Backend
    participant DB as SIEM DB
    participant ML as ML Detector
    participant Rules as Detection Rules
    participant Corr as Correlation Engine
    participant IO as Socket.IO
    participant SF as SIEM Frontend

    BB->>SIEM: POST /api/events (event data + API key)
    SIEM->>SIEM: Validate API key
    SIEM->>SIEM: Deduplicate (check external_id)
    SIEM->>SIEM: Normalize event type & status
    SIEM->>DB: Save SecurityEvent
    SIEM->>IO: Emit 'new_event'
    IO->>SF: Dashboard counter updates

    SIEM->>ML: Analyze event (7 features)
    ML-->>SIEM: anomaly_score, is_anomaly

    SIEM->>Rules: Evaluate 5 basic detection rules
    SIEM->>Corr: Evaluate 6 correlation rules
    
    alt Rule Triggered
        Rules-->>SIEM: Alert data
        Corr-->>SIEM: Additional alert data
        SIEM->>SIEM: Check alert cooldown
        SIEM->>SIEM: Calculate risk score (0-100)
        SIEM->>DB: Save Alert
        SIEM->>SIEM: Correlate into Incident
        SIEM->>DB: Save/Update Incident
        SIEM->>IO: Emit 'new_alert'
        IO->>SF: Alert table updates
    end
```

---

# 32. Glossary

| Term | Simple Explanation | In VaultX |
|------|-------------------|-----------|
| **API** (Application Programming Interface) | A way for two computer programs to talk to each other using HTTP requests | Bank and SIEM communicate via REST APIs |
| **REST** (Representational State Transfer) | A design pattern for building web APIs using HTTP methods (GET, POST, PUT, DELETE) | All VaultX endpoints follow REST conventions |
| **JWT** (JSON Web Token) | A small encoded "ticket" that proves who you are, signed with a secret key | Bank and SIEM use JWT for authentication |
| **CORS** (Cross-Origin Resource Sharing) | A security mechanism that controls which websites can call your API | Flask-CORS allows the React frontend to call the Flask backend |
| **ORM** (Object-Relational Mapping) | A tool that lets you work with database tables as if they were Python objects | SQLAlchemy maps users, accounts, transactions to Python classes |
| **SQLAlchemy** | Python's most popular ORM library for working with databases | Both Bank and SIEM use Flask-SQLAlchemy |
| **PostgreSQL** | A powerful, open-source relational database management system | vaultx_bank and vaultx_siem databases |
| **SIEM** (Security Information and Event Management) | A system that collects security data, detects threats, and generates alerts | SentinelSIEM monitors the Bank application |
| **Event** | A record of something that happened (login, transfer, etc.) | Bank generates ~13 types of security events |
| **Alert** | A warning generated when a detection rule identifies suspicious activity | SIEM creates alerts for brute force, compromise, etc. |
| **Severity** | How dangerous an alert is: LOW, MEDIUM, HIGH, or CRITICAL | Brute Force = HIGH, Account Compromise = CRITICAL |
| **Socket.IO** | A library for real-time bidirectional communication using WebSockets | SIEM uses it to push live updates to the dashboard |
| **WebSocket** | A protocol that allows a browser and server to send messages to each other in real-time | Socket.IO uses WebSocket as its primary transport |
| **Detection Rule** | A condition that, when met, generates an alert | "5 failed logins in 5 minutes = brute force alert" |
| **Brute Force** | An attack where someone tries many passwords to guess the correct one | Detection Rule 1 catches this |
| **Authentication** | Proving who you are (login) | JWT + bcrypt in Bank, JWT in SIEM |
| **Authorization** | Determining what you're allowed to do | "admin" role can manage users; "user" role cannot |
| **Hashing** | Converting a password into a scrambled string that can't be reversed | bcrypt hashes Bank passwords |
| **Endpoint** | A specific URL that accepts API requests (e.g., POST /api/auth/login) | Bank has ~15 endpoints, SIEM has ~30+ endpoints |
| **Blueprint** | Flask's way of organizing routes into separate modules | auth_bp, user_bp, transactions_bp, etc. |
| **Background Thread** | Code that runs separately from the main program, not blocking user requests | SIEM push and event collector run in background threads |
| **Deduplication** | Ensuring the same event isn't processed twice | SIEM checks `external_id` before saving |
| **MITRE ATT&CK** | A knowledge base of cyberattack techniques used for classification | SIEM maps alerts to techniques like T1110 (Brute Force) |
| **Isolation Forest** | A machine learning algorithm that finds unusual patterns (anomalies) | SIEM uses it for behavioral anomaly detection |
| **Incident** | A group of related alerts representing a security campaign | Multiple brute force alerts from same IP = one incident |
| **Risk Score** | A number (0-100) representing the overall danger level of an alert | Calculated from 6 factors including severity and ML score |
| **SOC** (Security Operations Center) | A team or system that monitors and responds to security threats | SentinelSIEM is the SOC dashboard |
| **Collector** | A background process that gathers security data from external sources | SIEM's collector polls the Bank every 10 seconds |
| **Checkpoint** | A saved timestamp marking the last successfully processed event | SIEM stores `last_event_timestamp` in settings table |
| **Correlation Engine** | Advanced detection that analyzes multi-event patterns across time windows | Detects Password Spraying, Distributed Auth, Multi-Source attacks |
| **Alert Cooldown** | Mechanism to prevent duplicate alerts for the same pattern within a time window | Prevents alert fatigue from repeated identical detections |
| **Password Spraying** | Attack where one IP tries many different usernames with common passwords | Correlation Rule 2 detects this pattern |
| **Distributed Attack** | Attack spread across multiple source IPs targeting multiple users | Correlation Rule 3 detects coordinated distributed attacks |

---

# 33. Final Summary

## What VaultX Is

VaultX is a full-stack cybersecurity demonstration project consisting of two connected web applications: a simulated banking platform and a Security Information and Event Management (SIEM) system. It demonstrates how a real Security Operations Center monitors a live application for threats.

## Why It Is Useful

- Demonstrates real-world security monitoring concepts
- Shows how banking events become security alerts
- Implements both rule-based and ML-based threat detection
- Provides a complete end-to-end event pipeline
- Maps threats to the MITRE ATT&CK framework
- Supports real-time monitoring with Socket.IO

## How It Works

1. Users interact with the Bank (login, transfer, etc.)
2. The Bank generates structured security events for every action
3. Events are pushed to the SIEM in real-time and polled as a backup
4. The SIEM processes each event through: deduplication → normalization → IP intelligence → ML anomaly detection → basic rule-based detection (5 rules) → advanced correlation engine (6 rules) → risk scoring → alert creation → incident correlation → alert cooldown
5. The SOC dashboard displays everything in real-time

## Technologies Used

- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Socket.IO Client, Lucide React
- **Backend**: Python Flask, Flask-SQLAlchemy, Flask-SocketIO, Flask-Bcrypt
- **Database**: PostgreSQL (with SQLite fallback)
- **Authentication**: JWT + bcrypt
- **ML**: scikit-learn Isolation Forest
- **Communication**: REST API + WebSocket
- **Reporting**: ReportLab (PDF), CSV, JSON export
- **Detection**: 11 total rules (5 basic + 6 correlation), configurable thresholds via database

## Cybersecurity Concepts Demonstrated

- Authentication (JWT, bcrypt)
- Authorization (role-based access control)
- Security event logging and monitoring
- SIEM operations
- Rule-based threat detection (5 basic rules + 6 advanced correlation rules = 11 total)
- ML-based anomaly detection
- Risk scoring
- Alert lifecycle management
- Incident correlation
- MITRE ATT&CK mapping
- IP intelligence and geolocation
- Account lockout protection
- Audit trail logging
- Real-time security monitoring

## Current Limitations

- Runs locally only (not deployed to production)
- Two separate databases (Bank and SIEM) rather than a centralized log store
- ML model is basic (trains on limited history, uses synthetic baseline for fresh DBs)
- No HTTPS in development
- No rate limiting middleware (configured but not enforced via Flask-Limiter)
- No email notifications (only Discord/Slack webhooks)
- Single-server architecture (no horizontal scaling)

## Possible Future Improvements

- Docker Compose for one-command startup
- Nginx reverse proxy with HTTPS
- Centralized logging (ELK stack or similar)
- More detection rules (e.g., unusual transaction amounts, off-hours activity)
- ~~Advanced correlation rules (Password Spraying, Distributed Auth, etc.)~~ ✅ Done (6 correlation rules added)
- User behavior profiling over longer time windows
- Automated incident response (e.g., auto-lock accounts on critical alerts)
- Full-text search for events
- ~~Exportable PDF reports~~ ✅ Done (PDF, CSV, JSON export added)
- Multi-tenant support
- Load testing and performance optimization

---

# 37. IP Geolocation & Intelligence

## Overview

SentinelSIEM enriches every incoming security event with **approximate IP geolocation intelligence**. When a real event arrives from the VaultX Bank containing a `source_ip`, the SIEM resolves geographic information using the free ip-api.com service and caches the result.

**Important**: IP geolocation provides an *approximate* location associated with an IP address. It does **not** identify the exact physical location of a person or device. Results may be affected by VPNs, proxies, corporate networks, cloud providers, and mobile carriers.

## Architecture

```
VaultX Bank
    ↓
Security Event (source_ip)
    ↓
SentinelSIEM Event Ingestion
    ↓
IP Intelligence Service
    ├─ Private IP? → Local Network / Private IP
    ├─ Cached? → Return cached data (24-hour cache)
    └─ New public IP? → ip-api.com lookup → Cache to DB
    ↓
Geographic Enrichment
    ├─ IP details (country, city, ISP, ASN)
    ├─ Coordinates (latitude, longitude)
    └─ Associated users & event history
    ↓
Detection Engine
    ├─ Existing 5 basic rules + 6 correlation rules
    ├─ Geographic Rules:
    │   ├─ New Country for User
    │   └─ Impossible Travel Detection
    └─ Risk Score (with geographic factors)
    ↓
Alert → Incident → Socket.IO → Dashboard
```

## IP Geolocation Provider

The system uses **ip-api.com** (free tier) for IP geolocation:

- **URL**: `http://ip-api.com/json/{ip}?fields=...`
- **Rate limit**: 45 requests/minute (free tier)
- **Fields returned**: country, countryCode, regionName, city, lat, lon, isp, org, as, timezone
- **Cache duration**: 24 hours (configurable via `geo_cache_hours` setting)
- **No API key required** for the free tier

For production, you may switch to a paid provider (MaxMind, IPinfo, etc.) by modifying `ip_service.py`.

## Private IP Handling

Private/local IP addresses are handled correctly:

| IP Range | Classification |
|----------|----------------|
| `127.0.0.1`, `::1` | Localhost — no external lookup |
| `10.0.0.0/8` | Private Network |
| `172.16.0.0/12` | Private Network |
| `192.168.0.0/16` | Private Network |

These IPs are **never sent** to the external geolocation service.

## Database Schema Changes

### Enhanced `ip_intelligence` table

| Column | Type | Notes |
|--------|------|-------|
| `latitude` | FLOAT | Approximate latitude |
| `longitude` | FLOAT | Approximate longitude |
| `asn` | VARCHAR(30) | Autonomous System Number |
| `timezone` | VARCHAR(50) | IP timezone |
| `event_count` | INTEGER | Cached event count |
| `alert_count` | INTEGER | Cached alert count |
| `first_seen` | TIMESTAMP | First event from this IP |
| `last_seen` | TIMESTAMP | Most recent event from this IP |

## Geographic Anomaly Detection

### Rule 1: New Country for User

```text
Condition:  User authenticates from a country they have never
            been associated with before
MITRE:      T1078 (Valid Accounts)
Severity:   MEDIUM
Cooldown:   60 minutes
```

### Rule 2: Impossible Travel

```text
Condition:  User moves between two geographic locations at a
            speed exceeding the configurable threshold (default: 900 km/h)
MITRE:      T1078 (Valid Accounts)
Severity:   MEDIUM (>900 km/h) or HIGH (>2000 km/h)
Cooldown:   30 minutes
```

Uses haversine distance formula to calculate approximate distance between coordinates.

## New API Endpoints

### GET /api/ip-intelligence/<ip>

Detailed IP intelligence with associated users, event history, and geographic data.

### GET /api/ip-intelligence/<ip>/events

Paginated security events from a specific IP.

### GET /api/ip-intelligence/<ip>/alerts

Alerts triggered from a specific IP.

### GET /api/ip-intelligence/geo-map

All IPs with coordinates for map visualization.

### GET /api/ip-intelligence/geo-stats

Geographic statistics: top countries, top cities, private vs public count.

### GET /api/ip-intelligence/user/<username>/ips

All known IP addresses for a specific user.

## Frontend: IP Intelligence Page

The IP Intelligence Portal provides:

1. **IP Search**: Look up any IP address for geolocation data
2. **Overview Tab**: Network intelligence (ISP, ASN, timezone), associated users
3. **Activity Tab**: Full security event history from the IP
4. **Users Tab**: User activity breakdown from the IP
5. **Alerts Tab**: All alerts triggered from the IP
6. **Geographic Statistics**: Top countries, cities, public vs private IPs
7. **Recently Resolved IPs**: Quick access to cached IP records

## Risk Score Enhancement

The risk scoring system now includes geographic factors:

| Factor | Points | Condition |
|--------|--------|-----------|
| New Geographic Source | +15 | User authenticates from a new country |
| Impossible Travel | +10 | Physically implausible movement detected |
| Geographic Context | +3 | IP geolocation available (non-private) |

## Configuration

New settings available in System Settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `new_country_cooldown_mins` | 60 | Cooldown for New Country alerts |
| `impossible_travel_window_hours` | 2 | Time window for impossible travel |
| `impossible_travel_speed_kmh` | 900 | Speed threshold (km/h) |
| `geo_cache_hours` | 24 | Cache duration for IP lookups |

## Limitations

- IP geolocation is **approximate**, not exact physical tracking
- Free tier (ip-api.com) has rate limits (45 req/min)
- VPN/proxy/cloud IPs may show the provider's location, not the user's
- Private IPs (127.0.0.1, 10.x, 192.168.x) have no public geolocation
- Geographic anomaly detection is a risk signal, not definitive attack evidence
- Impossible travel may be triggered by VPN, mobile networks, or timezone changes

## How to Use

1. Navigate to **IP Intelligence** in the SIEM sidebar
2. Search any IP address for its geolocation profile
3. View associated users, event history, and alerts
4. Check Geographic Intelligence Summary for top countries/cities
5. Use Activity tab to investigate suspicious IP behavior
6. Geographic anomalies automatically appear as risk factors in alerts