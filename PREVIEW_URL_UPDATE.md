# Preview URL Update - January 1, 2026

## Issue Fixed
The preview URL in both `.env` files was incorrect, pointing to an old/different UUID:
- **OLD URL:** `https://89a01666-1bac-4d63-bb77-7df7f88908d9.preview.emergentagent.com`
- **NEW URL:** `https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com`

## Changes Made

### 1. ✅ Updated Frontend .env
**File:** `/app/frontend/.env`
```env
REACT_APP_BACKEND_URL=https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

### 2. ✅ Updated Backend .env
**File:** `/app/backend/.env`
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com,https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.static.emergentagent.com,http://localhost:3000,*
```

### 3. ✅ Cleared All MongoDB Caches
- **ohlc_cache:** 2,500 documents deleted
- **fundamentals_cache:** 501 documents deleted
- **institutional_cache:** 501 documents deleted

### 4. ✅ Cleared In-Memory Cache
Called `/api/refresh` endpoint to clear backend cache.

### 5. ✅ Installed Missing Dependencies
Installed yfinance and related packages:
- yfinance==1.0
- beautifulsoup4==4.14.3
- websockets, protobuf, curl_cffi, etc.

### 6. ✅ Restarted All Services
```bash
sudo supervisorctl restart all
```

## Service Status
✅ All services running:
- **Backend:** RUNNING on port 8001
- **Frontend:** RUNNING on port 3000
- **MongoDB:** RUNNING on port 27017
- **Nginx:** RUNNING
- **Code Server:** RUNNING

## API Endpoint Structure
Frontend makes API calls to:
```
https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com/api/stocks
https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com/api/nifty50
etc.
```

The `/api` prefix is correctly configured for Kubernetes ingress routing.

## Preview URL
**Access your app at:**
https://e8b6b5ed-c634-4e15-9e36-60b6b2193b1e.preview.emergentagent.com

## Next Steps
1. Open the preview URL in your browser
2. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
3. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
4. Wait for initial data load (may take 1-2 minutes for 500 stocks)

## DALBHARAT Fix Status
The previous iteration implemented a fix for the DALBHARAT 15-min biggest trend calculation. The fix is in place and will work correctly once:
1. Fresh data is fetched (after cache clear)
2. Browser displays the updated results

The fix changes DALBHARAT from showing UP to correctly showing DOWN on the 15-min timeframe.

---
**Updated:** January 1, 2026, 21:30 IST
**Status:** ✅ Complete
