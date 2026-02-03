# NIFTY50 Calculation Fix - February 3, 2026

## Problem Statement
NIFTY50 index calculations were incorrect due to mixing two different data sources:
- **Current price**: Used 15-minute interval data
- **Previous close**: Used daily interval data

This inconsistency caused incorrect change percentage calculations, especially noticeable on Sundays when 15-min data might not include the latest data while daily data does.

## Root Cause
In `server.py` (lines 1626-1647), the code was:
```python
hist = nifty.history(period="5d", interval="15m")  # 15-min data
current = float(hist["Close"].iloc[-1])            # Using 15-min for current

daily = nifty.history(period="5d", interval="1d")  # Daily data
prev_close = float(daily["Close"].iloc[-2])        # Using daily for previous
```

## Solution Implemented

### 1. Consistent Data Source (Lines 1626-1654)
Changed to use **daily data consistently** for all price calculations:

```python
# Get daily data FIRST (for prices and pivot)
daily = nifty.history(period="5d", interval="1d")

# Get 15-min data (still needed for blocks calculation)
hist = nifty.history(period="5d", interval="15m")

# Current price = last DAILY close
current = float(daily["Close"].iloc[-1])

# Previous close = second-last DAILY close
prev_close = float(daily["Close"].iloc[-2]) if len(daily) > 1 else current

# Calculate change
change_pct = round((current - prev_close) / prev_close * 100, 2)
```

### 2. Pivot Calculation Updated
Also updated pivot calculation to use daily data for consistency:

```python
# Pivot calculation using last DAILY candle
last_daily = daily.iloc[-1]
pivot = round((float(last_daily["High"]) + float(last_daily["Low"]) + float(last_daily["Close"])) / 3, 2)
```

### 3. Preview URL Updates
Updated both `.env` files with correct preview URL:
- **Frontend**: `REACT_APP_BACKEND_URL=https://5edfc0bf-4e38-4c01-9b12-d375a5468b20.preview.emergentagent.com`
- **Backend**: `PREVIEW_URL` and `CORS_ORIGINS` updated to match

## Files Modified
1. `/app/backend/server.py` (lines 1626-1654)
2. `/app/frontend/.env`
3. `/app/backend/.env`

## Impact
- **NIFTY50 value**: Now correctly uses last daily close
- **Change %**: Correctly calculates based on consistent daily data
- **Pivot**: Uses daily candle data for more accurate pivot levels
- **Biggest Trend**: Continues to use 15-min blocks (unchanged, as intended)
- **Advance/Decline**: Already using daily data (no changes needed)

## What Was NOT Changed
- Individual stock calculations (already correct)
- Advance/Decline calculation (already using daily data correctly)
- 15-minute blocks calculation (still uses 15-min data, which is correct)

## Testing
Backend endpoint tested successfully:
```bash
curl http://localhost:8001/api/nifty50
```

Response shows correct NIFTY50 data with consistent calculations.

## Verification
- ✅ Backend server running successfully
- ✅ MongoDB connected
- ✅ API endpoint returning data
- ✅ No errors in logs
- ✅ Daily data used consistently for price calculations
