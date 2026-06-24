# PU Academic Performance Tracker — Deployment Guide

## Architecture

```
Vercel (Free)                    Render (Free)
┌────────────────────┐           ┌─────────────────────────────┐
│  React / Next.js   │  HTTPS    │  FastAPI (Python)            │
│  frontend          │ ────────► │  - LightGBM model serving    │
│                    │           │  - PDF generation (reportlab) │
│  /login            │           │  - JWT authentication         │
│  /dashboard        │           │  - Faculty-scoped API         │
└────────────────────┘           └─────────────────────────────┘
```

**Why this split:** React (UI) runs on Vercel — a JavaScript-only platform.
Python (LightGBM model) cannot run on Vercel. The FastAPI backend on Render
serves predictions and PDFs; everything else is pure React.

---

## Step 1 — Prepare Your GitHub Repositories

Create **two** GitHub repositories:
- `pu-tracker-frontend` — copy the contents of `/frontend/`
- `pu-tracker-api`     — copy the contents of `/backend/`

Upload your four model artefacts into `pu-tracker-api/`:
- `best_model.pkl`
- `scaler.pkl`
- `feature_cols.json`
- `thresholds.json`

> **Important:** Add these to `.gitignore` if they are large or sensitive.
> Alternatively, set `ARTEFACT_DIR` to a mounted volume path on Render.

---

## Step 2 — Deploy the Backend to Render

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your `pu-tracker-api` repository
3. Set:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `JWT_SECRET` | Any long random string (e.g. generate at random.org) |
   | `ALLOWED_ORIGINS` | `https://your-app.vercel.app` (fill in after step 3) |
   | `DEAN_PASSWORD` | Your chosen dean password |
   | `HOD_FESAC_PASSWORD` | Your chosen HOD FESAC password |
   | `HOD_FBA_PASSWORD` | ... |
   | `HOD_FEHAS_PASSWORD` | ... |
   | `HOD_PSTM_PASSWORD` | ... |
   | `ADVISOR_FESAC_PASSWORD` | ... |
   | `ADVISOR_FBA_PASSWORD` | ... |
   | `ADVISOR_FEHAS_PASSWORD` | ... |
   | `ADVISOR_PSTM_PASSWORD` | ... |
5. Click **Deploy**. Note the URL shown (e.g. `https://pu-tracker-api.onrender.com`).
6. Test: open `https://pu-tracker-api.onrender.com/api/meta/health` — should return `{"status":"ok","model_ready":true}`.

---

## Step 3 — Deploy the Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your `pu-tracker-frontend` repository
3. Framework: **Next.js** (auto-detected)
4. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://pu-tracker-api.onrender.com` (from step 2) |
5. Click **Deploy**. Vercel gives you a URL like `https://pu-tracker-frontend.vercel.app`.
6. Go back to Render → your backend service → Environment Variables → update `ALLOWED_ORIGINS` to your Vercel URL. Redeploy.

---

## Step 4 — Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Copy your model artefacts (*.pkl, *.json) into this directory
uvicorn app.main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
# .env.local already set to http://localhost:8000
npm run dev
# App running at http://localhost:3000
```

---

## Default Passwords (development only — change in production)

| Role | Default Password |
|---|---|
| Dean of Students | `dean_2025` |
| HOD — FESAC | `hod_fesac_2025` |
| HOD — FBA | `hod_fba_2025` |
| HOD — FEHAS | `hod_fehas_2025` |
| HOD — PSTM | `hod_pstm_2025` |
| Academic Advisor — FESAC | `advisor_fesac_2025` |
| Academic Advisor — FBA | `advisor_fba_2025` |
| Academic Advisor — FEHAS | `advisor_fehas_2025` |
| Academic Advisor — PSTM | `advisor_pstm_2025` |

Override all of these via environment variables in Render (never in code).

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/meta/health` | None | Model ready check |
| GET | `/api/auth/roles` | None | List all roles |
| POST | `/api/auth/login` | None | Login, receive JWT |
| GET | `/api/meta/model-info` | Bearer | SHAP, fairness, metrics |
| POST | `/api/predict/individual` | Bearer | Single student prediction |
| POST | `/api/predict/simulate` | Bearer | What-If re-prediction |
| POST | `/api/predict/batch` | Bearer | CSV batch inference |
| POST | `/api/reports/student-pdf` | Bearer | Student PDF report |
| POST | `/api/reports/cohort-pdf` | Bearer | Cohort PDF report |

Full interactive docs at `/docs` (Swagger UI).

---

## Supervisor Demo Script

1. Open the Vercel URL → Login as **Dean of Students**
2. Click **Batch Inference** → Upload `PU_Demo_Student_Data.csv`
3. Show KPI cards updating, insights panel, faculty charts
4. Click **Faculty Analytics** → walk through all 5 sections
5. Click **Student Risk Predictions** → open a High Risk student card
6. Show the **What-If Simulator** — drag attendance slider up, show risk class improve live
7. Download a **PDF Report**
8. Sign out → log back in as **HOD — FESAC** → show they only see FESAC students
