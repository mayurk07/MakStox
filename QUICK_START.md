# UDTS Stock Analyzer - Quick Start Guide

## What You Need

1. Your Supabase service_role key for project: `lqodntgumcjwbdwvsprm`
   - **IMPORTANT**: Your current service key is for a different project!
   - Get the correct key at: https://app.supabase.com/project/lqodntgumcjwbdwvsprm/settings/api
   - Copy the **service_role** key (not the anon key)
   - Update the `.env` file with this key

## How to Run

### Option 1: Using the startup scripts (Easiest)

#### Terminal 1 - Start the Backend:
```bash
./start-backend.sh
```

#### Terminal 2 - Start the Frontend:
```bash
./start-frontend.sh
```

### Option 2: Manual startup

#### Terminal 1 - Backend:
```bash
cd backend
python3 server.py
```

#### Terminal 2 - Frontend:
```bash
cd frontend
npm install  # only needed first time
npm start
```

## Access the App

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### "Supabase credentials not found"
- Make sure you've added the correct service_role key to `.env`
- The key must be for project `lqodntgumcjwbdwvsprm` (check the "ref" in the JWT)

### Backend won't start
- Install dependencies: `pip install -r backend/requirements.txt --break-system-packages`

### Frontend won't start
- Install dependencies: `cd frontend && npm install`

## What This App Does

UDTS (Uptrend Detection & Timing System) analyzes Indian stocks (NIFTY 50/500) and identifies:
- Stocks in uptrends across multiple timeframes
- Support/resistance levels
- Institutional holdings (FII/DII)
- Fundamental metrics (PE, ROE, Debt/Equity)
- Real-time scoring and sorting

Data is cached in Supabase for faster performance!
