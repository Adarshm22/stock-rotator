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

## API
- `GET /row` — returns the current row and index
- `GET /health` — simple health check
