# NIFTY CSV Rotator

A simple Next.js frontend with a Python FastAPI backend. The backend reads `NIFTY_historical_data.csv` and serves a single row, rotating to the next row every 60 seconds. The frontend refreshes every minute to display the next row.

## Project Structure
- `frontend/` — Next.js app
- `backend/` — FastAPI API
- `NIFTY_historical_data.csv` — data source

## Quick Start

### Backend (FastAPI)
```powershell
Set-Location "c:\Users\adars\Desktop\stocks\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (Next.js)
```powershell
Set-Location "c:\Users\adars\Desktop\stocks\frontend"
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## Configuration
The frontend uses `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Example:
```powershell
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
```

The backend uses `ALLOWED_ORIGINS` to set CORS origins (comma-separated).

Example:
```powershell
$env:ALLOWED_ORIGINS="http://localhost:3000,https://your-vercel-app.vercel.app"
```

## API
- `GET /row` — returns the current row and index
- `GET /health` — simple health check

## Deployment

### GitHub
```powershell
Set-Location "c:\Users\adars\Desktop\stocks"
git remote add origin https://github.com/<your-username>/nifty-csv-rotator.git
git branch -M main
git push -u origin main
```

### Vercel (Frontend)
1. Import the GitHub repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Add env var `NEXT_PUBLIC_API_URL` pointing to your Railway backend URL.
4. Deploy.

`frontend/vercel.json` is included to let Vercel auto-detect Next.js.

### Railway (Backend)
1. Create a new project and select the same GitHub repo.
2. Set **Root Directory** to `backend`.
3. Add env var `ALLOWED_ORIGINS` with your Vercel URL.
4. Set start command:
	`uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy and copy the generated public URL.

`backend/railway.toml` includes the same start command for Railway.
