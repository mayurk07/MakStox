# 15-Min Biggest Trend Logic Fix - January 1, 2026

## Issue Summary
For stock DALBHARAT on Jan 1, 2026, the 15-min biggest trend was incorrectly shown as **UDTS UP** when it should have been **UDTS DOWN**.

## Root Cause
The old logic used the complex G1/R1/R2/G2 pattern matching with a "forming candle" concept that excluded the last candle from trend calculations. This caused incorrect block partitioning when consecutive red candles showed a clear downtrend.

### Example of the Bug:
```
Candles: [09:15 GREEN, 09:30 RED, 09:45 RED (big drop -26 points)]

Old Logic Result:
- All three candles grouped into one UP block
- Biggest trend: UP with power 26.00 ✗ WRONG!

Expected Result:
- Block 1 (UP): 09:15 to 09:30
- Block 2 (DOWN): 09:45 onwards (the big drop)
- Biggest trend: DOWN ✓ CORRECT!
```

## New Logic Implementation

The fix implements a **simpler, more intuitive logic** ONLY for 15-min biggest trend calculation:

### Algorithm:

1. **Start with first candle (9:15 AM)**
   - If GREEN → first block direction = "UP"
   - If RED → first block direction = "DOWN"

2. **Same color candles continue the same block**
   - UP block + GREEN candle → add to same block
   - DOWN block + RED candle → add to same block

3. **Opposite color triggers trend change check**
   
   **Case A: UP block, RED candle appears**
   - Check: `RED_candle.close < previous_GREEN_candle.open`?
   - If YES → Trend changes to DOWN, new block starts
   - If NO → Continue same UP block
   
   **Case B: DOWN block, GREEN candle appears**
   - Check: `GREEN_candle.close > previous_RED_candle.open`?
   - If YES → Trend changes to UP, new block starts
   - If NO → Continue same DOWN block

4. **Record all blocks and find biggest**
   - Power = max(all opens/closes) - min(all opens/closes)
   - Biggest trend = block with highest power (first occurrence if tie)
   - Support price = opening price of the first candle in that block

## Changes Made

**File:** `/app/backend/server.py`
**Function:** `calculate_15min_blocks()` (lines 725-815)

### Before (Complex UDTS Logic):
```python
def calculate_15min_blocks(candles: List[Dict]) -> List[Dict]:
    """Partition candles into UDTS blocks"""
    # Used complex G1/R1/R2/G2 pattern matching
    # Called calculate_udts() for each test block
    # Had "forming candle" concept that caused bugs
    ...
```

### After (Simplified Logic):
```python
def calculate_15min_blocks(candles: List[Dict]) -> List[Dict]:
    """
    Partition candles into blocks using simplified logic for 15-min biggest trend.
    
    Logic:
    1. Start with first candle color
    2. Same color continues block
    3. Opposite color checks for trend change:
       - UP + RED: check if RED.close < GREEN.open
       - DOWN + GREEN: check if GREEN.close > RED.open
    4. Calculate power as max - min of all opens/closes
    """
    # Simple, direct logic without complex pattern matching
    ...
```

## Test Results

### DALBHARAT Jan 1, 2026 (First 6 candles)

**Input Data:**
```
1. 09:15: O=2132.90, C=2147.50 [GREEN]
2. 09:30: O=2147.30, C=2146.40 [RED]
3. 09:45: O=2148.30, C=2122.30 [RED] ← BIG DROP of 26 points!
4. 10:00: O=2123.70, C=2118.80 [RED]
5. 10:15: O=2120.10, C=2119.10 [RED]
6. 10:30: O=2120.00, C=2122.70 [GREEN]
```

**New Logic Output:**
```
Block 1 (UP):   09:15 to 09:30, Power: 14.60, Support: 2132.90
Block 2 (DOWN): 09:45 to 10:15, Power: 29.50, Support: 2148.30 ← BIGGEST!
Block 3 (UP):   10:30 onwards,  Power: 2.70,  Support: 2120.00

✅ Biggest Trend: DOWN
✅ Power: 29.50
✅ Support Price: 2148.30 (opening of 09:45)
```

**Comparison:**

| Metric | Old Logic | New Logic | Status |
|--------|-----------|-----------|--------|
| Direction | UP | DOWN | ✅ Fixed |
| Power | 26.00 | 29.50 | ✅ Fixed |
| Support | 2132.90 | 2148.30 | ✅ Fixed |
| Block Composition | 09:15+09:30+09:45 (mixed) | 09:45+10:00+10:15 (pure down) | ✅ Fixed |

## User's Calculation Verified

User correctly identified:
- **Third candle (09:45):** open = 2148.30
- **Fourth candle (10:00):** close = 2118.80  
- **Power:** 2148.30 - 2118.80 = 29.50 ✓

The new logic now correctly captures this calculation!

## Impact

### What's Fixed:
- ✅ Biggest trend direction now correctly identifies major price movements
- ✅ Power calculations accurately reflect the price range
- ✅ Support prices correctly point to the start of the trend
- ✅ Blocks no longer mix opposing price movements

### What's Unchanged:
- ✅ All other timeframes (Monthly, Weekly, Daily, 1H) still use original UDTS logic
- ✅ Regular UDTS calculations for trend display remain the same
- ✅ Only the 15-min "biggest trend" calculation uses the new logic

## Files Modified

1. **`/app/backend/server.py`**
   - Modified `calculate_15min_blocks()` function (lines 725-815)
   - Simplified logic for better accuracy
   - Added detailed documentation

## Testing

Run these test scripts to verify the fix:

```bash
# Test with first 6 candles
python3 /app/test_new_15min_logic.py

# Test with all 24 candles
python3 /app/test_fix_verification.py
```

## Deployment

The fix has been deployed and the backend restarted:
```bash
sudo supervisorctl restart backend
```

Backend status: ✅ RUNNING

---

**Date:** January 1, 2026  
**Fixed by:** E1 Agent  
**Issue:** DALBHARAT 15-min biggest trend incorrectly shown as UP  
**Resolution:** Implemented simplified block calculation logic for 15-min timeframe  
**Status:** ✅ FIXED and VERIFIED
