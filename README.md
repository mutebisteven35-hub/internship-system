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

# Create venv only if it does not already exist
python -m venv .venv

# Install backend dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Create/update database tables
.\.venv\Scripts\python.exe manage.py migrate

# Optional: only if you want demo accounts and sample data
.\.venv\Scripts\python.exe manage.py seed

# Start backend server
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Frontend

Open another PowerShell window:

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\frontend

# Install frontend dependencies
npm.cmd install

# Start frontend server
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Sample Login Accounts

These accounts exist only after running:

```powershell
.\.venv\Scripts\python.exe manage.py seed
```

All seeded accounts use the password `Passw0rd!`.

| Role | Username | Email |
| --- | --- | --- |
| Admin | `admin` | `admin@iles.local` |
| Instructor | `instructor` | `instructor@iles.local` |
| Instructor | `instructor2` | `instructor2@iles.local` |
| Student | `student` | `student@iles.local` |
| Student | `student2` | `student2@iles.local` |

## Password Management

Logged-in users can use **Change Password** from the app navigation.

Users who cannot sign in can use **Forgot password?** on the login screen.

In this local MVP, the reset code is displayed on screen because email delivery is not configured.

## Database Configuration

The backend prefers `DATABASE_URL`, then PostgreSQL environment variables, then SQLite.

Using `DATABASE_URL`:

```powershell
$env:DATABASE_URL="postgres://iles:iles_password@127.0.0.1:5432/iles"
```

Or using PostgreSQL variables:

```powershell
$env:POSTGRES_DB="iles"
$env:POSTGRES_USER="iles"
$env:POSTGRES_PASSWORD="iles_password"
$env:POSTGRES_HOST="127.0.0.1"
$env:POSTGRES_PORT="5432"
```

Without those variables, Django automatically uses:

```text
backend/db.sqlite3
```

## Useful Commands

### Run Backend Tests

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\backend
.\.venv\Scripts\python.exe manage.py test
```

### Reseed Sample Data

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\backend
.\.venv\Scripts\python.exe manage.py seed
```

### Build Frontend for Production

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\frontend
npm.cmd run build
```

## Production Deployment

The project includes production-ready settings for public hosting.

- Django runs with `DEBUG=False` from environment variables.
- PostgreSQL is used through `DATABASE_URL`.
- Static files are collected and served with WhiteNoise.
- Gunicorn is included for running Django in production.
- CORS, CSRF, HTTPS redirect, secure cookies, and allowed hosts are controlled by environment variables.
- `render.yaml` defines a Render Blueprint for a Django backend, React static frontend, and PostgreSQL database.

## Render Deployment

Render can host:

- Django backend
- React/Vite frontend
- PostgreSQL database

### Steps

1. Push this project folder to GitHub.
2. Go to Render.
3. Create a new **Blueprint**.
4. Select your GitHub repository.
5. Render will read `render.yaml`.
6. Review the services before creating them.

The Blueprint creates:

```text
iles-backend
iles-frontend
iles-postgres
```

If Render gives different public URLs, update these values in `render.yaml` or in the Render dashboard:

- Frontend `VITE_API_BASE_URL`
- Backend `CORS_ALLOWED_ORIGINS`
- Backend `DJANGO_CSRF_TRUSTED_ORIGINS`
- Backend `DJANGO_ALLOWED_HOSTS`

## Render Commands

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

## After Deploying

Run migrations on the deployed backend:

```bash
python backend/manage.py migrate
```

Create a real admin account:

```bash
python backend/manage.py createsuperuser
```

Do **not** run this in production unless you intentionally want demo/test data online:

```bash
python backend/manage.py seed
```

## Vercel Deployment

Vercel can host the React frontend and the Django backend, but you still need an external PostgreSQL database such as Neon or Supabase.

Create two Vercel projects from the same GitHub repository:

- one project for `frontend`
- one project for `backend`

### 1. Create PostgreSQL

Create a PostgreSQL database on Neon or Supabase, then copy the database connection string.

It should look similar to:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

### 2. Deploy Backend on Vercel

In Vercel, import the GitHub repository and configure the backend project:

```text
Root Directory: backend
Framework Preset: Other / Django if shown
Build Command: leave default unless Vercel asks
Output Directory: leave empty
Install Command: pip install -r requirements.txt
```

Add these backend environment variables in Vercel:

```text
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.vercel.app
DATABASE_URL=your-postgres-connection-string
CORS_ALLOWED_ORIGINS=https://your-frontend-project.vercel.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-frontend-project.vercel.app,https://your-backend-project.vercel.app
DJANGO_SECURE_SSL_REDIRECT=False
```

### 3. Deploy Frontend on Vercel

Import the same GitHub repository again and configure the frontend project:

```text
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

Add this frontend environment variable:

```text
VITE_API_BASE_URL=https://your-backend-project.vercel.app/api
```

### 4. Run Production Migrations

After the backend is deployed, run migrations from your laptop against the production PostgreSQL database:

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\backend
$env:DATABASE_URL="your-postgres-connection-string"
$env:DJANGO_SECRET_KEY="replace-with-a-long-random-secret"
$env:DJANGO_DEBUG="False"
$env:DJANGO_ALLOWED_HOSTS=".vercel.app"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Do not run seed unless you want demo/sample data online:

```powershell
.\.venv\Scripts\python.exe manage.py seed
```

If your Vercel project URLs change, update:

- frontend `VITE_API_BASE_URL`
- backend `CORS_ALLOWED_ORIGINS`
- backend `DJANGO_CSRF_TRUSTED_ORIGINS`

## Optional PostgreSQL With Docker

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES
docker compose up -d db
```

Then set:

```powershell
$env:DATABASE_URL="postgres://iles:iles_password@127.0.0.1:5432/iles"
```

Then run:

```powershell
cd C:\Users\USER\OneDrive\Documents\ILES\backend
.\.venv\Scripts\python.exe manage.py migrate
```

## Notes for Windows

Use:

```powershell
npm.cmd
```

instead of:

```powershell
npm
```

because PowerShell may block `npm.ps1`.

Example:

```powershell
npm.cmd install
npm.cmd run dev
```
