# INTERNSHIP LOGGING AND EVALUATION SYSTEM (ILES) MVP

INTERNSHIP LOGGING AND EVALUATION SYSTEM (ILES) is a local MVP for managing student placements, host organizations, workplace supervisors, daily logbooks, attendance records, evaluations, notifications, academic setup, and audit workflow records.

## Stack

- Backend: Django, Django REST Framework, token authentication
- Frontend: ReactJS with Vite
- Database: PostgreSQL when configured, SQLite fallback at `backend/db.sqlite3`

## Quick Start

### Backend

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver 127.0.0.1:8000
```

If PowerShell blocks venv activation, run the Python executable directly:

```powershell
C:\Users\USER\OneDrive\Documents\ILES\backend\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Frontend

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Sample Login Accounts

All seeded accounts use the password `Passw0rd!`.

| Role | Username | Email |
| --- | --- | --- |
| Admin | `admin` | `admin@iles.local` |
| Instructor | `instructor` | `instructor@iles.local` |
| Instructor | `instructor2` | `instructor2@iles.local` |
| Student | `student` | `student@iles.local` |
| Student | `student2` | `student2@iles.local` |

## Password Management

Logged-in users can use **Change password** from the app navigation. Users who cannot sign in can use **Forgot password?** on the login screen. In this local MVP, the reset code is displayed on screen because email delivery is not configured.

## Database Configuration

The backend prefers `DATABASE_URL`, then PostgreSQL environment variables, then SQLite.

```powershell
$env:DATABASE_URL="postgres://iles:iles_password@127.0.0.1:5432/iles"
```

or:

```powershell
$env:POSTGRES_DB="iles"
$env:POSTGRES_USER="iles"
$env:POSTGRES_PASSWORD="iles_password"
$env:POSTGRES_HOST="127.0.0.1"
$env:POSTGRES_PORT="5432"
```

Without those variables, Django automatically uses `backend/db.sqlite3`.

## Useful Commands

```powershell
# Backend tests using SQLite fallback
cd C:\Users\USER\OneDrive\Documents\ILES\backend
python manage.py test

# Reseed sample data
python manage.py seed

# Frontend production build
cd C:\Users\USER\OneDrive\Documents\ILES\frontend
npm.cmd run build
```

## Production Deployment

The project now includes production-ready settings for public hosting:

- Django runs with `DEBUG=False` from environment variables.
- PostgreSQL is used through `DATABASE_URL`.
- Static files are collected and served with WhiteNoise.
- Gunicorn is included for running Django in production.
- CORS, CSRF, HTTPS redirect, secure cookies, and allowed hosts are controlled by environment variables.
- `render.yaml` defines a Render Blueprint for a Django backend, React static frontend, and PostgreSQL database.

### Render Blueprint

1. Push this folder to a GitHub/GitLab repository.
2. In Render, create a new Blueprint from the repository.
3. Review service names and pricing before creating the resources.
4. If Render gives different public URLs, update these values in `render.yaml` or the Render dashboard:
   - Frontend `VITE_API_BASE_URL`
   - Backend `CORS_ALLOWED_ORIGINS`
   - Backend `DJANGO_CSRF_TRUSTED_ORIGINS`
   - Backend `DJANGO_ALLOWED_HOSTS`

The backend build command is:

```bash
bash backend/build.sh
```

The backend start command is:

```bash
cd backend && gunicorn iles_backend.wsgi:application --bind 0.0.0.0:$PORT
```

The frontend build command is:

```bash
cd frontend && npm install && npm run build
```

The frontend publish directory is:

```text
frontend/dist
```

After deploying, run the seed command once from the backend service shell if you want demo users online:

```bash
python backend/manage.py seed
```

## Optional PostgreSQL With Docker

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES
docker compose up -d db
```

Then set `DATABASE_URL=postgres://iles:iles_password@127.0.0.1:5432/iles` before running migrations.
