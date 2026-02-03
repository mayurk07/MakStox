# Bug Explanation: DALBHARAT 15-min Biggest Trend Incorrectly Shown as UP

## Summary
The biggest trend for DALBHARAT on Jan 1, 2026 is shown as **UP** (power 26.00) when it should be **DOWN** (power ~28.50).

## Root Cause
The bug is in the **`calculate_udts` function** when **G1 is not found** and it uses the alternative logic. The alternative logic treats the **last candle as "forming"** and excludes it from the trend calculation, which is incorrect when testing blocks during partitioning.

## Detailed Analysis

### Actual Data for Jan 1, 2026 (First 6 candles)
```
1. 09:15: O=2132.90, C=2147.50 [GREEN]  
2. 09:30: O=2147.30, C=2146.40 [RED]
3. 09:45: O=2148.30, C=2122.30 [RED]  ← BIG DROP of 26 points!
4. 10:00: O=2123.70, C=2118.80 [RED]
5. 10:15: O=2120.10, C=2119.10 [RED]
6. 10:30: O=2120.00, C=2122.70 [GREEN]
```

### How Blocks Are Currently Partitioned (WRONG)

**Block 1 (UP):** 09:15, 09:30, 09:45
- Power: max(2148.30, 2147.50, 2147.30, 2146.40, 2148.30, 2122.30) - min(...) = 2148.30 - 2122.30 = 26.00
- This block includes the big DROP candle (09:45) in an UP block!

**Block 2 (DOWN):** 10:00, 10:15
- Power: 4.90

**Result:** Biggest trend = Block 1 (UP) with power 26.00 ✗ WRONG!

### How Blocks Should Be Partitioned (CORRECT)

**Block 1 (UP):** 09:15 only
- Just the first green candle

**Block 2 (DOWN):** 09:30, 09:45, 10:00, 10:15
- All the consecutive red candles showing the downtrend
- Power: 2148.30 - 2118.80 = 29.50
  (Highest open: 2148.30 from 09:45, Lowest close: 2118.80 from 10:00)

**Result:** Biggest trend = Block 2 (DOWN) with power 29.50 ✓ CORRECT!

### Why the Bug Occurs

When the block partitioning algorithm tests adding candle 3 (09:45 RED) to the current block [09:15 GREEN, 09:30 RED]:

1. **Test block:** [09:15 GREEN, 09:30 RED, 09:45 RED]

2. **Calculate UDTS for test block:**
   - Loop backwards looking for G1 (green candle with close > previous red's open)
   - Check position 2 (09:45 RED) - skip, it's red
   - Check position 1 (09:30 RED) - skip, it's red  
   - Check position 0 (09:15 GREEN) - it's green!
     - Look backwards for previous red - **NONE FOUND** (it's the first candle)
   - **G1 = None** (no valid G1/R1 pattern found)

3. **Alternative logic when G1 = None:**
   ```python
   closed_candles = candles[:-1] if len(candles) > 1 else []
   # closed_candles = [09:15, 09:30]  (excludes last candle 09:45!)
   
   oldest_closed = closed_candles[0]   # 09:15
   newest_closed = closed_candles[-1]  # 09:30
   price_diff = newest_closed["close"] - oldest_closed["open"]
   # price_diff = 2146.40 - 2132.90 = 13.50 >= 0
   direction = "UP"  # ✗ WRONG!
   ```

4. **The Problem:**
   - The alternative logic excludes the last candle (09:45) treating it as "forming"
   - But 09:45 is a **MASSIVE RED CANDLE** dropping 26 points!
   - By ignoring it, the calculation only sees 09:15 → 09:30 which is slightly up
   - So UDTS returns "UP" when it should be "DOWN"

5. **Block partition decision:**
   - Current block direction: UP
   - Test UDTS result: UP
   - Same direction → **ADD 09:45 to the UP block** ✗ WRONG!

### The Core Issue

The "forming candle" concept (excluding last candle) is appropriate when:
- Calculating UDTS for a stock's **actual current state**
- The last candle in the array is literally still forming in real-time

But it's **WRONG** when:
- Testing blocks during partitioning
- ALL candles in the test block are historical/closed
- We need to see the complete picture including the last candle

### User's Expected Calculation

User correctly identified:
- Candle 2 (09:30): O=2147.30
- Candle 3 (09:45): O=2148.30, C=2122.30  
- Candle 4 (10:00): C=2118.80
- These should form one DOWN block
- Power = 2148.30 - 2118.80 = 29.50 (or 2147.30 - 2118.80 = 28.50 depending on interpretation)

## Solution

The `calculate_udts` function needs to have different behavior when:
1. **Normal mode:** Exclude last candle as forming (current behavior)
2. **Block testing mode:** Include ALL candles in the calculation

OR

The block partitioning logic should not rely on the "closed_candles" concept in `calculate_udts` and should analyze all candles in the test block.

## Impact

This bug causes:
- Incorrect biggest trend detection (wrong direction and wrong block)
- Misleading trading signals
- Power calculations that don't reflect the actual price movement
- Blocks that mix up and down movements illogically

## Test Case

```python
candles = [
    {"open": 2132.90, "close": 2147.50},  # GREEN (+14.60)
    {"open": 2147.30, "close": 2146.40},  # RED (-0.90)
    {"open": 2148.30, "close": 2122.30},  # RED (-26.00) BIG DROP!
]

result = calculate_udts(candles)
# Current (WRONG): returns "UP" 
# Expected: should return "DOWN"
```

---
**Date:** January 1, 2026  
**Stock:** DALBHARAT  
**Timeframe:** 15-min  
**Severity:** HIGH - Affects trading decision logic
