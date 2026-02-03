# Auto-Refresh Logic Update

## Date: January 31, 2026

## Change Summary
Updated the auto-refresh timing to trigger at exact 15-minute intervals: **:00, :15, :30, and :45 minutes** of every hour.

## Previous Behavior
- Auto-refresh triggered at: **:01, :16, :31, :46 minutes**
- Would refresh 1 minute after the quarter-hour marks

## New Behavior
- Auto-refresh triggers at: **:00, :15, :30, :45 minutes**
- Refreshes exactly at the quarter-hour marks

## Implementation Details

**File Modified:** `/app/frontend/src/App.js`
**Lines:** 380-437

### Key Changes:

1. **Target Minutes Updated:**
   ```javascript
   // OLD: const targetMinutes = [1, 16, 31, 46];
   // NEW: const targetMinutes = [0, 15, 30, 45];
   ```

2. **Enhanced Precision:**
   - Added millisecond precision to ensure exact timing
   - Now accounts for `currentMilliseconds` in calculation
   - Formula: `msToNext = (minutesToNext * 60 - currentSeconds) * 1000 - currentMilliseconds`

3. **Improved Logging:**
   - Console now shows the exact scheduled time (not just minutes remaining)
   - Format: "Next auto-update scheduled at [TIME] (in X minutes)"

### Unchanged Features (Working Correctly):
✅ Auto-refresh **only starts after** initial data load is complete
✅ Waits for `initialDataLoaded` flag to be true
✅ Does NOT interfere with initial 8-12 minute data loading process
✅ Recursive scheduling ensures continuous operation

## Example Timeline

If current time is **10:37:23**:
- Next refresh: **10:45:00** (in ~7.6 minutes)

If current time is **10:00:05**:
- Next refresh: **10:15:00** (in ~15 minutes)

If current time is **10:52:00**:
- Next refresh: **11:00:00** (in 8 minutes)

## Testing

**Service Status:**
```bash
frontend    RUNNING   pid 4458
```

**Compilation:**
```
Compiled successfully!
webpack compiled successfully
```

## User Impact
- More intuitive refresh timing aligned with quarter-hour marks
- Better synchronization with market data updates
- Clearer console logging for debugging

## Files Modified
- `/app/frontend/src/App.js` - Updated auto-refresh schedule logic
