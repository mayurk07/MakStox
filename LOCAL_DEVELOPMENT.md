# Local Development Setup

This guide explains how to run the UDTS Stock Analyzer locally after the Supabase migration.

---

## Prerequisites

- Python 3.11+ installed
- Node.js 16+ and npm installed
- Supabase account (free tier)
- Git

---

## Step 1: Get Supabase Credentials

You need two keys from your Supabase project:

### 1.1 Get Supabase URL and Anon Key
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key

### 1.2 Get Service Role Key
1. In the same **API** page
2. Under **Project API keys**, find **service_role**
3. Click to reveal and copy it
4. ⚠️ **Keep this secret!** This key has admin access.

---

## Step 2: Configure Environment Variables

Edit the `.env` file in the project root:

```env
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_SUPABASE_ANON_KEY=your-anon-key-here

# Backend Supabase credentials
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

Replace the placeholders with your actual Supabase credentials.

---

## Step 3: Start Backend

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start the backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

The backend will start at: `http://localhost:8001`

**Verify it's working**:
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "supabase",
  "db_status": "connected"
}
```

---

## Step 4: Start Frontend

Open a new terminal:

```bash
# Install npm dependencies
cd frontend
npm install

# Start the development server
npm start
```

The frontend will start at: `http://localhost:3000`

Your browser should automatically open to the application.

---

## Step 5: Test the Application

1. **Load Stock Data**:
   - The app will automatically start fetching 500 stocks
   - First load takes 8-12 minutes
   - Progress is shown in the UI

2. **Check Database**:
   - Go to Supabase Dashboard → Table Editor
   - You should see data appearing in:
     - `ohlc_cache`
     - `fundamentals_cache`
     - `institutional_cache`
     - `stock_lists`

3. **Test Features**:
   - Filter stocks by UDTS trend
   - Sort by columns
   - Apply numeric filters (ROE, PE, etc.)
   - Refresh data using the Refresh button

---

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'supabase'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

---

### Database connection fails

**Error**: `Supabase not available` in logs

**Solution**:
1. Check that `SUPABASE_SERVICE_ROLE_KEY` is set in `.env`
2. Verify the key is correct (no extra spaces)
3. Check that your Supabase project is active (not paused)

---

### Frontend can't connect to backend

**Error**: Network errors in browser console

**Solution**:
1. Verify backend is running on port 8001
2. Check `REACT_APP_API_URL` in frontend code points to `http://localhost:8001`
3. Check CORS settings in backend (should allow `*` for local development)

---

### First load taking too long

**Behavior**: Stock data loading for more than 15 minutes

**Solution**:
- This is expected for the FIRST load (500 stocks)
- Check backend logs to see progress
- Subsequent loads will be instant (< 5 seconds) thanks to caching

---

## Development Tips

### Backend Logs
Backend logs show:
- Database connection status
- Stock fetching progress
- Cache hits/misses
- API requests

Example log output:
```
INFO:     Supabase connected successfully
INFO:     Starting BATCH PARALLEL analysis of 500 stocks (20 stocks per batch)
INFO:     Processing batch 1/25 (20 stocks)
INFO:     Using RELIANCE from Supabase cache
```

### Hot Reload
- **Backend**: Auto-reloads on code changes (thanks to `--reload` flag)
- **Frontend**: Auto-reloads on code changes (built into Create React App)

### Clear Cache
To force fresh data fetch:
```bash
curl http://localhost:8001/api/refresh
```

Or use the **Refresh** button in the UI.

### Database Inspection
View cached data in Supabase:
1. Go to Supabase Dashboard
2. Click **Table Editor**
3. Select a table (e.g., `ohlc_cache`)
4. Browse the data

---

## Project Structure

```
project/
├── backend/
│   ├── server.py          # FastAPI application
│   ├── database.py        # Supabase operations
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   └── ...
│   ├── package.json      # npm dependencies
│   └── ...
├── .env                  # Environment variables
├── render.yaml           # Render deployment config
├── vercel.json           # Vercel deployment config
├── DEPLOYMENT_GUIDE.md   # Production deployment
└── README.md             # Project overview
```

---

## Next Steps

Once local development is working:

1. **Test all features** thoroughly
2. **Push to GitHub** repository
3. **Deploy to production** using [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

## Common Commands

**Backend**:
```bash
# Start backend
cd backend && uvicorn server:app --reload --port 8001

# Check health
curl http://localhost:8001/health

# Clear cache
curl http://localhost:8001/api/refresh

# Get stock data
curl http://localhost:8001/api/stocks
```

**Frontend**:
```bash
# Start frontend
cd frontend && npm start

# Build for production
cd frontend && npm run build

# Run tests
cd frontend && npm test
```

**Database**:
```bash
# View Supabase logs
# Go to: https://supabase.com/dashboard → Your Project → Logs

# Query data (using Supabase SQL Editor)
SELECT * FROM ohlc_cache LIMIT 10;
SELECT COUNT(*) FROM fundamentals_cache;
```

---

## Support

If you encounter issues:
1. Check backend logs in terminal
2. Check browser console for frontend errors
3. Check Supabase dashboard logs
4. Review [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) for changes made
5. See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for deployment help

---

**Happy Coding!** 🚀
