# UDTS Logic Update - January 2025

## Summary
Updated the `calculate_udts` function in `/app/backend/server.py` to improve the logic when G1 candle is not found.

## Changes Made

### Location
**File:** `/app/backend/server.py`  
**Function:** `calculate_udts` (lines 590-607)

### Previous Logic (When G1 Not Found)
```python
if g1_idx is None:
    last_closed = candles[-1]
    direction = "UP" if is_green(last_closed) else "DOWN"
    return {"direction": direction, "g1": None, "r1": None, "r2": None, "g2": None}
```

**Issue:** Simply looked at the last candle's color, which doesn't work well for:
- Brand new stocks with only forming candles
- Stocks without clear G1/R1 patterns

### New Logic (When G1 Not Found)

#### Case (a): No Closed Candles
If the stock is brand new with only 1 forming candle:
- **GREEN forming candle → UDTS UP**
- **RED forming candle → UDTS DOWN**

#### Case (b): Has Closed Candles  
If there's at least one closed candle:
- Calculate: `price_diff = newest_closed["close"] - oldest_closed["open"]`
- **If price_diff >= 0 → UDTS UP**
- **If price_diff < 0 → UDTS DOWN**

**Note:** When only 1 closed candle exists, newest = oldest (same candle), so it compares close vs open of that candle.

### Implementation
```python
if g1_idx is None:
    # No G1 found - use alternative logic
    # Check if there are any closed candles (all candles except the last one which is forming)
    closed_candles = candles[:-1] if len(candles) > 1 else []
    
    if len(closed_candles) == 0:
        # Case (a): No closed candles - use forming candle's color
        forming_candle = candles[-1]
        direction = "UP" if is_green(forming_candle) else "DOWN"
    else:
        # Case (b): At least one closed candle exists
        # Compare newest closed candle's close vs oldest closed candle's open
        oldest_closed = closed_candles[0]
        newest_closed = closed_candles[-1]
        price_diff = newest_closed["close"] - oldest_closed["open"]
        direction = "UP" if price_diff >= 0 else "DOWN"
    
    return {"direction": direction, "g1": None, "r1": None, "r2": None, "g2": None}
```

## Testing

All test cases passed successfully:

✅ **Test 1:** Brand new stock with 1 GREEN forming candle → UP  
✅ **Test 2:** Brand new stock with 1 RED forming candle → DOWN  
✅ **Test 3:** 1 closed + 1 forming (uptrend) → UP  
✅ **Test 4:** 1 closed + 1 forming (downtrend) → DOWN  
✅ **Test 5:** Multiple closed candles (net uptrend) → UP  
✅ **Test 6:** Multiple closed candles (net downtrend) → DOWN  
✅ **Test 7:** Normal G1 found scenario → Original logic works  

## Benefits

1. **Better handling of new stocks:** Properly handles stocks with minimal history
2. **More accurate trend determination:** Uses price action across all closed candles instead of just the last one
3. **Maintains backward compatibility:** Original G1/R1/R2/G2 logic remains unchanged when G1 is found

## Notes

- The logic applies to all timeframes: Monthly, Weekly, Daily, 1H, 15min
- "Closed candles" = all candles except the last one (which is still forming)
- "In scope candles" are already filtered before being passed to `calculate_udts`
- When only 1 closed candle exists, oldest = newest = that same candle

---
**Date:** January 1, 2025  
**Updated by:** E1 Agent  
**Verified:** All test cases passing
