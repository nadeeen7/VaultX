# VaultX Bank + SentinelSIEM — Production Deployment Guide

> **Phase 2: Deployment Preparation**  
> This guide covers deploying all four services to production. Do NOT deploy until you have reviewed and approved the hosting platform choices.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Required Environment Variables](#3-required-environment-variables)
4. [Database Setup](#4-database-setup)
5. [Bank Backend Deployment](#5-bank-backend-deployment)
6. [SIEM Backend Deployment](#6-siem-backend-deployment)
7. [Bank Frontend Deployment](#7-bank-frontend-deployment)
8. [SIEM Frontend Deployment](#8-siem-frontend-deployment)
9. [Connecting Production URLs](#9-connecting-production-urls)
10. [CORS Configuration](#10-cors-configuration)
11. [HTTPS Verification](#11-https-verification)
12. [Socket.IO / WebSocket Verification](#12-socketio--websocket-verification)
13. [Bank → SIEM Communication Testing](#13-bank--siem-communication-testing)
14. [Common Deployment Problems](#14-common-deployment-problems)
15. [Rollback Considerations](#15-rollback-considerations)

---

## 1. Prerequisites

### Infrastructure Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.11+ (tested with 3.11.8) |
| **Node.js** | 18+ (for frontend builds) |
| **PostgreSQL** | 14+ (two separate databases required) |
| **HTTPS** | Required for all production URLs |

### Hosting Services (4 separate deployments)

| Service | Type | Purpose |
|---------|------|---------|
| Bank Backend | Python/Flask API | Banking REST API |
| Bank Frontend | Static SPA (React) | Banking web application |
| SIEM Backend | Python/Flask + Socket.IO | SIEM API + real-time events |
| SIEM Frontend | Static SPA (React) | SOC dashboard |

### Recommended Hosting Platforms

- **Backends**: Render, Railway, Fly.io, or any PaaS supporting Python + PostgreSQL
- **Frontends**: Vercel, Netlify, Cloudflare Pages, or static hosting on any PaaS
- **Database**: Managed PostgreSQL (Render PostgreSQL, Supabase, Neon, AWS RDS, etc.)

---

## 2. Architecture Overview

```
┌──────────────────────┐         ┌──────────────────────┐
│   Bank Frontend      │         │   SIEM Frontend      │
│   (React + Vite)     │         │   (React + Vite)     │
│   Static SPA         │         │   Static SPA         │
└──────────┬───────────┘         └──────────┬───────────┘
           │ HTTPS API                       │ HTTPS API + WSS
           ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│   Bank Backend       │◄───────►│   SIEM Backend       │
│   Flask + Gunicorn   │  API    │   Flask + Socket.IO  │
│   Port from env      │         │   + eventlet         │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                 │
           ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│   vaultx_bank DB     │         │   vaultx_siem DB     │
│   PostgreSQL          │         │   PostgreSQL          │
└──────────────────────┘         └──────────────────────┘
```

### Data Flow

1. **User → Bank Frontend → Bank Backend**: Standard banking operations
2. **Bank Backend → SIEM Backend**: Security events sent via REST API (server-to-server)
3. **SIEM Backend → SIEM Frontend**: Real-time updates via Socket.IO (WebSocket)
4. **User → SIEM Frontend → SIEM Backend**: SOC analyst operations

---

## 3. Required Environment Variables

### ⚠️ SECRET GENERATION

Generate strong secrets before deployment:

```bash
# Generate a 64-character hex string for SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a different one for JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a strong API key for SIEM communication
python -c "import secrets; print(secrets.token_hex(32))"
```

**⚠️ NEVER commit generated secrets to Git. NEVER use the example values below in production.**

### Bank Backend (Environment Variables)

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `DATABASE_URL` | ✅ | `postgresql://user:pass@host:5432/vaultx_bank` | PostgreSQL connection with SSL |
| `SECRET_KEY` | ✅ | *(generated hex string)* | Flask session secret |
| `JWT_SECRET_KEY` | ✅ | *(generated hex string)* | JWT token signing key |
| `CORS_ORIGINS` | ⏳ | `https://bank.yourdomain.com` | Comma-separated allowed origins. Leave empty initially; add when frontend is deployed. |
| `SIEM_API_URL` | ⏳ | `https://siem-api.yourdomain.com` | SIEM backend URL. Leave empty initially; add when SIEM is deployed. |
| `SIEM_API_KEY` | ⏳ | *(generated hex string)* | Shared API key with SIEM backend. Add when SIEM is deployed. |
| `PORT` | ⚙️ | `5000` | Server port (most platforms set this automatically) |
| `MAX_LOGIN_ATTEMPTS` | ⚙️ | `5` | Account lockout threshold |
| `LOCKOUT_DURATION_MINUTES` | ⚙️ | `15` | Lockout duration |
| `RATE_LIMIT_PER_MINUTE` | ⚙️ | `60` | API rate limit |

> **Legend:** ✅ = Required at startup, ⏳ = Optional — Bank works without it, add later, ⚙️ = Optional with default

### SIEM Backend (Environment Variables)

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `DATABASE_URL` | ✅ | `postgresql://user:pass@host:5432/vaultx_siem` | PostgreSQL connection with SSL |
| `SECRET_KEY` | ✅ | *(generated hex string)* | Flask session secret |
| `JWT_SECRET_KEY` | ✅ | *(generated hex string)* | JWT token signing key |
| `CORS_ORIGINS` | ✅ | `https://siem.yourdomain.com,https://bank.yourdomain.com` | Allowed origins |
| `SIEM_API_KEY` | ✅ | *(same key as Bank's SIEM_API_KEY)* | Shared API key for Bank→SIEM |
| `SECUREBANK_API_URL` | ✅ | `https://bank-api.yourdomain.com/api/security-events` | Bank API URL for polling |
| `SECUREBANK_API_KEY` | ✅ | *(same key as Bank's SIEM_API_KEY)* | Bank API authentication |
| `SECUREBANK_POLL_INTERVAL` | ⚙️ | `10` | Polling interval in seconds |
| `PORT` | ⚙️ | `5001` | Server port |
| `DISCORD_WEBHOOK_URL` | ⚙️ | *(empty)* | Optional alert notifications |
| `SLACK_WEBHOOK_URL` | ⚙️ | *(empty)* | Optional alert notifications |

### Bank Frontend (Build-Time Variables)

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `VITE_API_URL` | ✅ | `https://bank-api.yourdomain.com` | Bank backend API URL |

### SIEM Frontend (Build-Time Variables)

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `VITE_API_URL` | ✅ | `https://siem-api.yourdomain.com` | SIEM backend API URL |
| `VITE_SOCKET_URL` | ✅ | `wss://siem-api.yourdomain.com` | Socket.IO WebSocket URL |
| `VITE_BANK_API_URL` | ⚙️ | `https://bank-api.yourdomain.com` | Bank API URL (sidebar display) |

> **⚠️ VITE_* variables are PUBLIC** — they are embedded in the frontend JavaScript bundle. Never put secrets, passwords, or API keys in VITE_* variables.

---

## 4. Database Setup

### Overview

The project uses **two separate PostgreSQL databases**:

| Database | Used By | Purpose |
|----------|---------|---------|
| `vaultx_bank` | Bank Backend | Users, accounts, transactions, security events |
| `vaultx_siem` | SIEM Backend | Alerts, incidents, MITRE mapping, IP intelligence |

### Table Creation

Both backends **automatically create tables on startup** using SQLAlchemy's `db.create_all()`. No migration step is required for initial deployment.

- **Bank Backend**: Creates tables in `vaultx_bank` on first run
- **SIEM Backend**: Creates tables in `vaultx_siem`, seeds default users (admin/analyst/viewer) and MITRE techniques

### Database Initialization Steps

1. Create two PostgreSQL databases on your managed provider
2. Create separate database users with appropriate permissions
3. Set the `DATABASE_URL` environment variable for each backend
4. Start each backend — tables are created automatically
5. **For Bank demo data** (optional): Run `python seed.py` in the Bank backend directory after first startup

### SSL Configuration

Most managed PostgreSQL providers require SSL connections. Append `?sslmode=require` to your `DATABASE_URL`:

```
DATABASE_URL=postgresql://user:pass@host:5432/vaultx_bank?sslmode=require
```

### Important Notes

- Do NOT expose PostgreSQL ports to the public internet
- Use connection pooling (PgBouncer) for high-traffic deployments
- Keep regular database backups
- The SIEM backend has SQLite fallback — in production, ensure PostgreSQL is always available

---

## 5. Bank Backend Deployment

### Production Start Command

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app
```

Or using the Procfile: `web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app`

### Deployment Steps

1. Create a new deployment service for the Bank Backend
2. Set the **root directory** to `bank/backend`
3. Set the **build command**: `pip install -r requirements.txt`
4. Set the **start command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app`
5. Configure the 3 required environment variables: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`
6. Deploy and verify: `GET https://your-bank-api.yourdomain.com/api/health`
7. **Later**, when the SIEM backend is deployed, add `SIEM_API_URL` and `SIEM_API_KEY`
8. **Later**, when the frontend is deployed, add `CORS_ORIGINS`

### Post-Deployment

After the backend is running and connected to PostgreSQL:

```bash
# Optional: seed demo data
python seed.py
```

### Key Files

| File | Purpose |
|------|---------|
| `run.py` | Application entry point |
| `app/app.py` | Flask application factory |
| `config/config.py` | Configuration classes |
| `requirements.txt` | Python dependencies |
| `Procfile` | Production start command |
| `runtime.txt` | Python version specification |

---

## 6. SIEM Backend Deployment

### Production Start Command

```bash
gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 run:app
```

Or using the Procfile: `web: gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 run:app`

### ⚠️ Critical: Socket.IO Requirements

- **Must use `eventlet` worker class** (not default sync workers)
- **Must use exactly 1 worker** (Socket.IO requires shared state)
- **Must NOT use multiple workers** (breaks real-time event broadcasting)

### Deployment Steps

1. Create a new deployment service for the SIEM Backend
2. Set the **root directory** to `siem/backend`
3. Set the **build command**: `pip install -r requirements.txt`
4. Set the **start command**: `gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 run:app`
5. Configure all required environment variables (see Section 3)
6. Deploy and verify: `GET https://your-siem-api.yourdomain.com/api/health`

### What Happens on First Start

The SIEM backend automatically:
1. Creates all database tables
2. Seeds MITRE ATT&CK technique mappings
3. Creates default SOC users:
   - `admin` / `admin123` (Admin role)
   - `analyst` / `analyst123` (Security Analyst role)
   - `viewer` / `viewer123` (Viewer role)
4. Starts the background SecureBank event collector

### Post-Deployment

- **Change default passwords immediately** after first login
- The background collector starts automatically and polls the Bank API

### Key Files

| File | Purpose |
|------|---------|
| `run.py` | Application entry point |
| `app/__init__.py` | Flask application factory |
| `app/config.py` | Configuration classes |
| `app/database.py` | Database + Socket.IO initialization |
| `requirements.txt` | Python dependencies |
| `Procfile` | Production start command |
| `runtime.txt` | Python version specification |

---

## 7. Bank Frontend Deployment

### Build & Deploy

```bash
cd bank/frontend
VITE_API_URL=https://bank-api.yourdomain.com npm run build
# Deploy the contents of the dist/ directory
```

### Deployment Steps

1. Create a new deployment service for the Bank Frontend (static site)
2. Set the **root directory** to `bank/frontend`
3. Set the **build command**: `VITE_API_URL=https://bank-api.yourdomain.com npm run build`
4. Set the **output directory**: `dist`
5. Deploy

### Environment Variables (Build-Time)

Set `VITE_API_URL` during the build step. This is the only required variable.

### SPA Routing

Configure your hosting provider to redirect all routes to `index.html` (SPA fallback) so that client-side routing works correctly.

---

## 8. SIEM Frontend Deployment

### Build & Deploy

```bash
cd siem/frontend
VITE_API_URL=https://siem-api.yourdomain.com \
VITE_SOCKET_URL=wss://siem-api.yourdomain.com \
VITE_BANK_API_URL=https://bank-api.yourdomain.com \
npm run build
# Deploy the contents of the dist/ directory
```

### Deployment Steps

1. Create a new deployment service for the SIEM Frontend (static site)
2. Set the **root directory** to `siem/frontend`
3. Set the **build command** with all VITE_* variables:
   ```
   VITE_API_URL=https://siem-api.yourdomain.com VITE_SOCKET_URL=wss://siem-api.yourdomain.com VITE_BANK_API_URL=https://bank-api.yourdomain.com npm run build
   ```
4. Set the **output directory**: `dist`
5. Deploy

### Environment Variables (Build-Time)

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | SIEM backend API URL |
| `VITE_SOCKET_URL` | Socket.IO WebSocket URL (must use `wss://` for HTTPS) |
| `VITE_BANK_API_URL` | Bank API URL (displayed in sidebar) |

### SPA Routing

Configure your hosting provider to redirect all routes to `index.html` (SPA fallback).

---

## 9. Connecting Production URLs

After all four services are deployed, update the environment variables to connect them:

### Example URL Configuration

```
# Bank Frontend:  https://bank.yourdomain.com
# Bank Backend:   https://bank-api.yourdomain.com
# SIEM Frontend:  https://siem.yourdomain.com
# SIEM Backend:   https://siem-api.yourdomain.com
```

### Connection Map

| From | To | Variable | Value |
|------|----|----------|-------|
| Bank Frontend | Bank Backend | `VITE_API_URL` | `https://bank-api.yourdomain.com` |
| SIEM Frontend | SIEM Backend | `VITE_API_URL` | `https://siem-api.yourdomain.com` |
| SIEM Frontend | SIEM Backend (WS) | `VITE_SOCKET_URL` | `wss://siem-api.yourdomain.com` |
| SIEM Frontend | Bank Backend (display) | `VITE_BANK_API_URL` | `https://bank-api.yourdomain.com` |
| Bank Backend | SIEM Backend | `SIEM_API_URL` | `https://siem-api.yourdomain.com` |
| SIEM Backend | Bank Backend | `SECUREBANK_API_URL` | `https://bank-api.yourdomain.com/api/security-events` |

### Update Process

1. Deploy all four services
2. Update `CORS_ORIGINS` on both backends to include the frontend URLs
3. Update `SIEM_API_URL` on Bank backend and `SECUREBANK_API_URL` on SIEM backend
4. Rebuild frontends with correct `VITE_*` URLs
5. Test all connections

---

## 10. CORS Configuration

### Phased Approach

**Initial deployment (Bank only):** Leave `CORS_ORIGINS` empty or unset. The Bank backend will block all cross-origin requests — this is fine because there is no frontend deployed yet. API calls from server-side tools or `curl` are not affected by CORS.

**After frontend is deployed:** Set `CORS_ORIGINS` to your frontend URL:

```
CORS_ORIGINS=https://bank.yourdomain.com
```

Only the Bank frontend origin should be allowed.

### SIEM Backend

```
CORS_ORIGINS=https://siem.yourdomain.com,https://bank.yourdomain.com
```

Both frontend origins are allowed because:
- SIEM frontend makes API calls
- Bank frontend accesses the public security-events endpoint

### ⚠️ Never Use in Production

```bash
# NEVER do this:
CORS_ORIGINS=*
```

Wildcard CORS with authentication/JWT is a security vulnerability. The Bank backend will refuse to start with wildcard CORS in production — if `CORS_ORIGINS` is empty, all cross-origin requests are blocked.

---

## 11. HTTPS Verification

### Requirements

- All production URLs MUST use HTTPS
- Socket.IO MUST use WSS (WebSocket Secure) in production
- No mixed HTTP/HTTPS content

### Verification Steps

1. Open each frontend URL — verify HTTPS lock icon in browser
2. Open browser DevTools → Network tab
3. Verify all API requests use `https://`
4. Verify Socket.IO connection uses `wss://`
5. Check for mixed content warnings in browser console

### SSL Certificates

Most PaaS providers (Render, Vercel, Netlify, etc.) handle SSL certificates automatically. If using a custom domain:

- Ensure DNS is configured correctly
- Wait for certificate issuance (can take up to 24 hours)
- Verify certificate chain is complete

---

## 12. Socket.IO / WebSocket Verification

### Requirements

- SIEM backend must use eventlet worker class with gunicorn
- Only 1 worker instance allowed
- Frontend must connect to WSS endpoint

### Verification Steps

1. Open SIEM frontend in browser
2. Open browser DevTools → Network tab → WS filter
3. Verify WebSocket connection is established
4. Perform a bank action (e.g., login) — verify real-time event appears in SIEM dashboard
5. Check Socket.IO connection status in the SIEM sidebar

### Troubleshooting

If Socket.IO fails to connect:
1. Verify `VITE_SOCKET_URL` uses `wss://` (not `ws://`)
2. Verify `CORS_ORIGINS` includes the SIEM frontend URL
3. Verify the SIEM backend is running with eventlet worker
4. Check that your hosting platform supports WebSocket connections

---

## 13. Bank → SIEM Communication Testing

### Overview

The Bank backend sends security events to the SIEM backend via REST API. The SIEM backend also polls the Bank backend as a backup mechanism.

### Verification Steps

1. **Check Bank → SIEM direct push**: Log in to Bank frontend → Check SIEM events page for the login event
2. **Check SIEM collector polling**: SIEM backend logs should show `[SecureBank Collector]` messages
3. **Verify shared API key**: Both `SIEM_API_KEY` (Bank) and `SECUREBANK_API_KEY` (SIEM) must match
4. **Check health endpoints**:
   - Bank: `GET https://bank-api.yourdomain.com/api/health`
   - SIEM: `GET https://siem-api.yourdomain.com/api/health`

### Troubleshooting

If events aren't flowing from Bank to SIEM:
1. Verify `SIEM_API_URL` on Bank backend points to SIEM backend
2. Verify `SECUREBANK_API_URL` on SIEM backend points to Bank backend
3. Verify both use the same `SIEM_API_KEY` / `SECUREBANK_API_KEY` value
4. Check CORS — SIEM backend must allow the Bank backend origin
5. Check network connectivity between the two backends

---

## 14. Common Deployment Problems

### Problem: "Connection refused" or "ECONNREFUSED"

**Cause**: Backend not running or wrong URL configured.  
**Fix**: Verify the backend health endpoint responds. Check `VITE_API_URL` matches the actual backend URL.

### Problem: CORS errors in browser console

**Cause**: Backend CORS_ORIGINS doesn't include the frontend URL.  
**Fix**: Update `CORS_ORIGINS` on the backend to include the exact frontend origin (with `https://` and no trailing slash).

### Problem: Socket.IO won't connect

**Cause**: Wrong worker class, missing WSS, or CORS issue.  
**Fix**: Ensure gunicorn uses `--worker-class eventlet`, `VITE_SOCKET_URL` uses `wss://`, and CORS includes the frontend origin.

### Problem: "JWT token expired" immediately

**Cause**: Clock skew between servers or mismatched `JWT_SECRET_KEY`.  
**Fix**: Ensure both backends use the same secret (if sharing tokens). Verify server clocks are synchronized (NTP).

### Problem: Database connection fails on startup

**Cause**: Wrong `DATABASE_URL`, PostgreSQL not reachable, or SSL required.  
**Fix**: Test connection with `psql`. Add `?sslmode=require` if using managed PostgreSQL. Ensure firewall allows the connection.

### Problem: Frontend shows blank page

**Cause**: SPA routing not configured.  
**Fix**: Configure your hosting provider to serve `index.html` for all routes (SPA fallback / rewrite rules).

### Problem: Tables not created

**Cause**: Database permissions or wrong database name.  
**Fix**: Ensure the database user has CREATE TABLE permissions. Check `DATABASE_URL` points to the correct database.

---

## 15. Rollback Considerations

### Before Deploying

1. **Database**: Take a backup before deployment if the database already has data
2. **Environment variables**: Save the current working `.env` configuration
3. **Code**: Tag the current commit: `git tag pre-production-v1`

### Rollback Steps

1. If the new deployment fails, revert to the previous code version
2. Restore the previous environment variables
3. Redeploy
4. If database migrations were run, restore from backup

### Zero-Downtime Deployment

For zero-downtime deployments:
1. Deploy the new backend version alongside the old one
2. Verify the new version works
3. Switch traffic to the new version
4. Shut down the old version

---

## Appendix: Service Summary

| Service | Port | Start Command | Health Check |
|---------|------|---------------|--------------|
| Bank Backend | $PORT (5000) | `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app` | `GET /api/health` |
| SIEM Backend | $PORT (5001) | `gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 run:app` | `GET /api/health` |
| Bank Frontend | 80/443 | Static file serving | N/A |
| SIEM Frontend | 80/443 | Static file serving | N/A |

### Recommended Deployment Order

1. **Database** — Create both PostgreSQL databases
2. **SIEM Backend** — Deploy first (it creates tables + seeds data)
3. **Bank Backend** — Deploy second (creates tables + optionally seed data)
4. **Bank Frontend** — Build with `VITE_API_URL` pointing to Bank backend
5. **SIEM Frontend** — Build with all three `VITE_*` variables
6. **CORS Update** — Update CORS_ORIGINS on both backends with final frontend URLs
7. **Rebuild Frontends** — If CORS origins changed, rebuild and redeploy frontends
8. **End-to-End Test** — Verify all connections work

---

> **This is Phase 2 preparation only. Do NOT deploy until you have explicitly approved the hosting platform and configuration.**
