# Weekly Candle "In Scope" Logic Fix

## Date: January 15, 2025

## Problem Statement
The weekly timeframe "in scope candles" logic had a bug where the last weekly candle was being INCLUDED on Thursday even when the time was ≤3:30PM. This was incorrect behavior.

## Required Logic
INCLUDE the last candle on the weekly timeframe as "in scope" IF:
- **(Thursday AND time is after 3:30PM)** OR
- **(Friday, Saturday, or Sunday - any time)** OR  
- **(Monday AND time is before 9:15AM)**

EXCLUDE the last candle in all other cases.

## Bugs Found

### Bug 1: Thursday Logic (Line 566-567)
**Before:**
```python
elif weekday == 3 and not market_closed:  # Thursday after market open
    return candles
```
- Used `not market_closed` which means "market is OPEN"
- This incorrectly INCLUDED the candle when market was open on Thursday
- Should have used `market_closed` to check if time is after 3:30PM

**After:**
```python
elif weekday == 3 and market_closed:  # Thursday after 3:30PM
    return candles
```

### Bug 2: Missing Saturday and Sunday (Line 564)
**Before:**
```python
if weekday == 4:  # Friday
    return candles
```
- Only checked for Friday (weekday == 4)
- Missed Saturday (weekday == 5) and Sunday (weekday == 6)

**After:**
```python
if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
    return candles
```

### Bug 3: Monday Logic (Line 568-569)
**Before:**
```python
elif weekday == 0 and market_closed:  # Monday before market open
    return candles[:-1] if len(candles) > 1 else []
```
- Used generic `market_closed` check which is True both before 9:15AM and after 3:30PM
- This would EXCLUDE on Monday before 9:15AM (wrong) and INCLUDE on Monday after 3:30PM (also wrong)

**After:**
```python
elif weekday == 0 and (hour < 9 or (hour == 9 and minute < 15)):  # Monday before 9:15AM
    return candles
```
- Specifically checks if time is before 9:15AM on Monday
- Now correctly INCLUDES only when time is before 9:15AM

## File Changed
- `/app/backend/server.py` - Lines 543-586 (function `get_in_scope_candles`)

## Testing
Created comprehensive test script `/app/test_weekly_candle_fix.py` that validates 25 different scenarios:
- ✅ All 25 tests PASSED
- Verified correct behavior for all days of the week
- Verified correct behavior for various times on each day
- Confirmed the specific edge cases mentioned in requirements

## Test Results Summary
```
Thursday 2:00 PM (market open)      → EXCLUDE ✅
Thursday 3:29 PM (still open)       → EXCLUDE ✅
Thursday 3:30 PM (closed)           → INCLUDE ✅
Thursday 4:00 PM (closed)           → INCLUDE ✅
Friday (any time)                   → INCLUDE ✅
Saturday (any time)                 → INCLUDE ✅
Sunday (any time)                   → INCLUDE ✅
Monday 12:00 AM - 9:14 AM           → INCLUDE ✅
Monday 9:15 AM onwards              → EXCLUDE ✅
Monday 3:30 PM (after close)        → EXCLUDE ✅
Tuesday (any time)                  → EXCLUDE ✅
Wednesday (any time)                → EXCLUDE ✅
```

## Impact
This fix ensures that:
1. Weekly candles are correctly included/excluded based on the exact time and day requirements
2. UDTS calculations for weekly timeframe will now use the correct set of candles
3. The bug reported (Thursday ≤3:30PM incorrectly including last candle) is resolved

## Verification
To verify the fix works correctly in production:
1. Monitor the application on Thursday before 3:30PM - last weekly candle should be EXCLUDED
2. Monitor the application on Thursday after 3:30PM - last weekly candle should be INCLUDED
3. The fix is backward compatible and doesn't affect other timeframes (monthly, daily, 1hour, 15min)
