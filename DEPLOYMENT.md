# RiskIntel upay — Deployment & Live Hosting Guide

This guide details the complete deployment topology for **RiskIntel upay** across cloud platforms.

- **GitHub Repository:** [https://github.com/mdsayadulislam/riskintel-upay](https://github.com/mdsayadulislam/riskintel-upay)
- **Live Frontend (Vercel):** [https://riskintel-upay.vercel.app](https://riskintel-upay.vercel.app)
- **Live Backend API (Render):** [https://riskintel-upay.onrender.com](https://riskintel-upay.onrender.com)
- **API Swagger Documentation:** [https://riskintel-upay.onrender.com/docs](https://riskintel-upay.onrender.com/docs)

---

## 1. Architecture Topology

```
┌──────────────────────────────────────────────┐
│  Client Browser / Evaluator Mobile Simulator │
└──────────────────────┬───────────────────────┘
                       │ HTTPS
                       ▼
┌──────────────────────────────────────────────┐
│  Frontend: Next.js 14 on Vercel              │
│  Domain: https://riskintel-upay.vercel.app   │
└──────────────────────┬───────────────────────┘
                       │ REST API + JWT Bearer
                       │ Strict CORS Allowlist
                       ▼
┌──────────────────────────────────────────────┐
│  Backend: FastAPI + LightGBM + SHAP on Render│
│  Domain: https://riskintel-upay.onrender.com │
└──────────────────────┬───────────────────────┘
                       │ WAL Mode
                       ▼
┌──────────────────────────────────────────────┐
│  Persistent Audit DB: SQLite (WAL)           │
│  Zero-PII / Zero-Secret Security Ledger      │
└──────────────────────────────────────────────┘
```

---

## 2. Deploying Backend on Render (FastAPI + LightGBM)

Render hosts the Python FastAPI gateway, LightGBM inference model, and persistent SQLite WAL database.

### Method A: 1-Click Blueprint Deploy (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository: `https://github.com/mdsayadulislam/riskintel-upay`.
4. Render will automatically detect `render.yaml` and configure all build/start commands and environment variables.
5. Click **Apply**.

### Method B: Manual Web Service Setup
1. Click **New +** > **Web Service**.
2. Select repository: `mdsayadulislam/riskintel-upay`.
3. Set the following fields:
   - **Name:** `riskintel-upay`
   - **Environment:** `Python 3`
   - **Region:** Singapore / Frankfurt / Oregon
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt && python backend/train_pipeline.py`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   ```env
   RISKINTEL_ENV=production
   JWT_SECRET_KEY=generate-a-strong-random-hex-string
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ALLOWED_ORIGINS=https://riskintel-upay.vercel.app,http://localhost:3000
   DATABASE_PATH=data/riskintel_audit.db
   RATE_LIMIT_ASSESS_PER_MIN=60
   RATE_LIMIT_AUTH_PER_MIN=10
   ```
5. Click **Create Web Service**.
6. Note your service URL: `https://riskintel-upay.onrender.com`.

---

## 3. Deploying Frontend on Vercel (Next.js 14)

Vercel hosts the edge-rendered Next.js 14 web application.

### Step-by-Step Vercel Deployment:
1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** > **Project**.
3. Import the GitHub repository: `mdsayadulislam/riskintel-upay`.
4. In **Configure Project**:
   - **Framework Preset:** `Next.js`
   - **Root Directory:** Click `Edit` and select `frontend`.
5. Under **Environment Variables**, add:
   ```env
   NEXT_PUBLIC_API_URL=https://riskintel-upay.onrender.com
   ```
   *(Or leave blank/point to your live Render URL. If not provided, it falls back to local or mock endpoints).*
6. Click **Deploy**.
7. In ~60 seconds, your site will be live at `https://riskintel-upay.vercel.app` (or your assigned Vercel URL).

---

## 4. Deploying via Docker (Local or Cloud Server)

Both backend and frontend can be spun up simultaneously using `docker-compose`:

```bash
# Clone the repository
git clone https://github.com/mdsayadulislam/riskintel-upay.git
cd riskintel-upay

# Build and start all services in detached mode
docker-compose up --build -d

# Check running status
docker-compose ps
```

- **Frontend:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`

---

## 5. Automated CI/CD (GitHub Actions)

Every commit pushed to the `main` branch of `https://github.com/mdsayadulislam/riskintel-upay` triggers an automated GitHub Actions workflow (`.github/workflows/ci.yml`) that:
1. Sets up Python 3.10 and installs dependencies.
2. Trains the LightGBM model and verifies SHAP TreeExplainer generation.
3. Executes the full `pytest backend/tests/test_security.py` security suite (18/18 tests).
4. Sets up Node.js 18.x and compiles the Next.js production build (`npm run build`).
