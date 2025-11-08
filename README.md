## Chinese Tutoring System

A role-based scheduling app for Chinese tutoring built with Flask (API) and React (Vite). Tutors publish availability; students browse and book 20‑minute sessions. Authentication is powered by Clerk. Data is stored with SQLAlchemy (SQLite by default).

### Tech stack
- Backend: Flask, SQLAlchemy, Flask-CORS, Clerk backend API
- Frontend: React (Vite), Clerk React, Tailwind + shadcn/ui
- DB: SQLite (default, file-based)

---

## Quick start (local)

### 1) Backend — Python virtual environment

```bash
# From repo root
cd backend

# Create & activate venv (macOS/Linux, zsh/bash)
python3 -m venv .venv
source .venv/bin/activate

# Install backend requirements
pip install -r requirements.txt

# Environment variables (example)
export SECRET_KEY="dev-secret-key"
export CLERK_SECRET_KEY="sk_live_or_test_from_clerk"
# Optional: DATABASE_URL (defaults to sqlite:///app.db inside backend/)
# export DATABASE_URL="sqlite:///app.db"

# Run the API (creates tables automatically)
python app.py
# Server starts on http://localhost:5001
```

Health check:
```bash
curl http://localhost:5001/api/health
```

### 2) Frontend — Vite dev server

```bash
# From repo root
cd frontend
npm install

# Create local env file
cat > .env.local << 'EOF'
VITE_API_URL=http://localhost:5001
VITE_CLERK_PUBLISHABLE_KEY=pk_live_or_test_from_clerk
EOF

# Start dev server
npm run dev
# App opens at http://localhost:5173
```

Important: The backend enforces authorized parties for Clerk at `http://localhost:5173`. Run the frontend on that port for local development.

---

## Configuration

### Backend environment variables
- `SECRET_KEY`: Flask secret key (string)
- `DATABASE_URL` (optional): SQLAlchemy URI (defaults to `sqlite:///app.db`)
- `CLERK_SECRET_KEY`: Clerk Backend Secret (required for auth)
- `CLERK_PUBLISHABLE_KEY` (optional): surfaced for completeness; used mainly by frontend

Location: export in your shell before running `python app.py`.  
SQLite DB file is created on first run (default `backend/app.db`). A sample DB file may exist in `backend/instance/app.db`.

### Frontend environment variables
- `VITE_API_URL`: Backend URL (e.g., `http://localhost:5001`)
- `VITE_CLERK_PUBLISHABLE_KEY`: Clerk Publishable Key for the React app

Location: `frontend/.env.local`

---

## Common workflows

### Create a tutor’s availability (tutor role)
1) Sign in via the frontend (Clerk)  
2) For tutors: open Sessions → “Add Availability”  
3) Fill date, start/end time (20‑minute increments), type (online/in‑person), and toggle recurring if needed  
4) Save; the weekly calendar and monthly summary will reflect the new availability

### Book a session (student role)
1) Sign in (Clerk) and complete onboarding  
2) Select a tutor card, view weekly availability  
3) Click an available 20‑minute slot → Confirm booking in the dialog  
4) Slot becomes booked; sessions list updates

---

## Project structure (partial)
```text
backend/
  app.py                 # Flask app (CORS, blueprints, auth wiring)
  auth.py                # Clerk auth decorator (require_auth)
  config.py              # Config (SECRET_KEY, DATABASE_URL, Clerk keys)
  models.py              # SQLAlchemy models
  routes/
    availability.py      # Availability CRUD
    sessions.py          # Booking + session feeds
  requirements.txt       # Python dependencies

frontend/
  src/
    App.jsx              # App shell + routing by role
    components/          # Sessions, Availability, Onboarding, UI
    services/api.js      # API client (uses VITE_API_URL)
  package.json
  .env.local             # Frontend env (VITE_*)
```

---

## Troubleshooting
- 401/403 on API: Ensure `CLERK_SECRET_KEY` is set for the backend and the frontend is sending a valid Clerk token (signed in).
- CORS/auth party errors: Keep the frontend on `http://localhost:5173` (default Vite port) during local dev.
- Missing env: Frontend requires `VITE_CLERK_PUBLISHABLE_KEY`; backend requires `CLERK_SECRET_KEY`.
- Timezone display: Backend normalizes to UTC; frontend renders in NYC-local presentation. Ensure your system clock is correct.

---

## Requirements files
- Python deps: `backend/requirements.txt`
  ```txt
  Flask==3.0.0
  Flask-SQLAlchemy==3.1.1
  Flask-CORS==4.0.0
  clerk-backend-api
  requests==2.31.0
  ```
- Node deps: managed by `frontend/package.json` via `npm install`

---

## Scripts cheat sheet
```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="dev-secret-key"
export CLERK_SECRET_KEY="sk_from_clerk"
python app.py

# Frontend
cd frontend
npm install
echo "VITE_API_URL=http://localhost:5001" > .env.local
echo "VITE_CLERK_PUBLISHABLE_KEY=pk_from_clerk" >> .env.local
npm run dev
```

---

