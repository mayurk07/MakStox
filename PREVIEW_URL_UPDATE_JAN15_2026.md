# Preview URL Update - January 15, 2026

## Update Summary
Updated both frontend and backend `.env` files to reflect the current preview URL for this session with the weekly candle logic fix.

## Changes Made

### ✅ Frontend .env Updated
**File:** `/app/frontend/.env`

**OLD:**
```env
REACT_APP_BACKEND_URL=https://column-repair.preview.emergentagent.com
```

**NEW:**
```env
REACT_APP_BACKEND_URL=https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com
```

### ✅ Backend .env Updated
**File:** `/app/backend/.env`

**OLD:**
```env
CORS_ORIGINS=https://b5968144-7df7-4f65-aa3d-5f2a0e869843.preview.emergentagent.com,https://b5968144-7df7-4f65-aa3d-5f2a0e869843.preview.static.emergentagent.com,http://localhost:3000,*
```

**NEW:**
```env
CORS_ORIGINS=https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com,https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.static.emergentagent.com,http://localhost:3000,*
```

### ✅ Services Restarted
```bash
sudo supervisorctl restart backend frontend
```

## Current Preview URL
**Access your application with the weekly candle fix at:**
```
https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com
```

## Service Status
✅ All services running and healthy:
- **Backend:** RUNNING on port 8001 - API healthy, MongoDB connected
- **Frontend:** RUNNING on port 3000
- **MongoDB:** RUNNING on port 27017
- **Nginx:** RUNNING
- **Code Server:** RUNNING

## Code Changes Included
This preview URL includes the **Weekly Candle "In Scope" Logic Fix** completed earlier:
- Fixed Thursday logic (now correctly checks after 3:30PM)
- Fixed weekend days (Friday, Saturday, Sunday all included)
- Fixed Monday logic (now specifically checks before 9:15AM)

## API Endpoints
Frontend correctly makes API calls to:
```
https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com/api/stocks
https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com/api/nifty50
https://a205079b-6d10-4266-b8d5-2c47ec03452d.preview.emergentagent.com/api/refresh
```

The `/api` prefix routes correctly to the backend via Kubernetes ingress.

## Testing the Fix
To verify the weekly candle logic fix is working:
1. Open the preview URL in your browser
2. Check any stock's weekly timeframe analysis
3. The fix ensures proper candle inclusion based on:
   - Thursday after 3:30PM ✅
   - Friday, Saturday, Sunday (any time) ✅
   - Monday before 9:15AM ✅

---
**Updated:** January 15, 2026
**Status:** ✅ Complete - Preview URL synchronized with current environment
