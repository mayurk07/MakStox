# Testing Instructions for Bug Fixes

## 🔧 Fixes Implemented

1. **Column Filters Now Exclude NULL/BLANK/"-" Values**
2. **Auto-Update Re-enabled (Only After First Data Load)**

---

## 🧪 Test Case #1: Column Filters Exclude Null/Blank Values

### Objective
Verify that when numeric column filters are applied, stocks with null/undefined/blank/"-" values are EXCLUDED from results.

### Steps to Test

#### 1.1 Load the Application
- Open your browser and navigate to the application URL
- Wait for the initial data load to complete (8-12 minutes on first load, <5 seconds on subsequent loads if cache exists)
- You should see a table with 500 NIFTY stocks

#### 1.2 View Unfiltered Data (Baseline)
- **Action**: Scroll through the table without applying any filters
- **Expected**: All 500 stocks are visible, including those with null/"-" values in various columns
- **Note**: Some stocks may show "-" or blank values for ROE, PE, PB, Revenue%, Earnings%, etc.

#### 1.3 Apply a Numeric Filter (Test ROE)
- **Action**: Click the "Show Column Filters" button at the top
- **Action**: In the ROE column filter section, enter:
  - **ROE Min**: `10`
  - (Leave ROE Max empty)
- **Action**: Press Enter or click outside the input field
- **Expected Results**:
  - ✅ Filtered stocks count decreases significantly
  - ✅ All visible stocks have ROE values >= 10
  - ✅ NO stocks with ROE = "-" or null or blank are shown
  - ✅ Scroll through results - confirm ALL stocks have valid ROE numeric values

#### 1.4 Test Multiple Filters (Test PE Ratio)
- **Action**: Keep ROE filter active, now add PE filter:
  - **PE Min**: (leave empty)
  - **PE Max**: `30`
- **Expected Results**:
  - ✅ Filtered stocks count decreases further
  - ✅ All visible stocks have ROE >= 10 AND PE <= 30
  - ✅ NO stocks with "-" or null values in ROE OR PE columns
  - ✅ Both filters work together correctly

#### 1.5 Test Range Filter (Test Market Cap)
- **Action**: Clear all filters (refresh page or manually clear inputs)
- **Action**: Apply Market Cap filter:
  - **Market Cap Min**: `50`
  - **Market Cap Max**: `500`
- **Expected Results**:
  - ✅ Only stocks with Market Cap between 50-500 thousand crores are shown
  - ✅ NO stocks with "-" or null Market Cap values are shown
  - ✅ All visible stocks have valid Market Cap within the range

#### 1.6 Test With Empty Results
- **Action**: Apply an extreme filter:
  - **ROE Min**: `100` (very high, unlikely to have many stocks)
- **Expected Results**:
  - ✅ Very few or zero stocks shown (depending on data)
  - ✅ NO stocks with null/"-" ROE values sneak through
  - ✅ Only stocks with actual ROE >= 100 are shown

#### 1.7 Clear Filters (Verify Reset)
- **Action**: Clear all filter inputs (delete values or refresh page)
- **Expected Results**:
  - ✅ All 500 stocks are visible again
  - ✅ Stocks with "-" or null values are now visible (when no filter is applied)
  - ✅ Confirms that null values are only excluded when filters are ACTIVE

### ✅ Test Case #1 Success Criteria
- [ ] When NO filter is applied → All stocks visible (including null/"-" values)
- [ ] When ANY numeric filter is applied → Stocks with null/"-" values in that column are EXCLUDED
- [ ] Multiple filters work together correctly
- [ ] Range filters (min + max) work correctly
- [ ] Clearing filters restores all stocks

---

## 🧪 Test Case #2: Auto-Update Only After First Data Load

### Objective
Verify that auto-update mechanism waits for initial data load to complete before starting the 15-minute update cycle.

### Steps to Test

#### 2.1 Open Browser Console
- **Action**: Press F12 to open Developer Tools
- **Action**: Navigate to the "Console" tab
- **Action**: Clear the console (click the 🚫 icon or press Ctrl+L)

#### 2.2 Load Application (Fresh)
- **Action**: Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R on Mac)
- **Expected Console Output**:
  ```
  Auto-update waiting for initial data load to complete...
  ```
- **Verify**: This message should appear IMMEDIATELY after page load
- **Verify**: The message indicates auto-update is waiting (not running yet)

#### 2.3 Wait for First Data Load
- **Action**: Wait for the stock data table to populate (8-12 minutes on first load, <5 seconds if cache exists)
- **Expected Console Output** (once data loads):
  ```
  Stocks response: {...}
  Next auto-update scheduled in X minutes
  ```
- **Verify**: The "Next auto-update scheduled" message appears AFTER data loads
- **Verify**: The X minutes value should be the time until next :01, :16, :31, or :46 minute mark

#### 2.4 Verify Auto-Update Schedule
- **Action**: Check the current time (e.g., 10:23)
- **Action**: Calculate next target time:
  - Current: 10:23 → Next target: 10:31 (31 minutes)
  - Current: 10:18 → Next target: 10:31 (31 minutes)
  - Current: 10:47 → Next target: 11:01 (1 minute of next hour)
- **Expected**: Console should show "Next auto-update scheduled in [correct value] minutes"
- **Example**: If it's 10:23 now, should show "Next auto-update scheduled in 8 minutes"

#### 2.5 Wait for Auto-Update to Trigger
- **Action**: Wait until the next scheduled time (e.g., wait until 10:31 if current is 10:23)
- **Keep Console Open**: Watch for messages
- **Expected Console Output** (at the scheduled time):
  ```
  Auto-update triggered at [HH:MM:SS AM/PM]
  Stocks response: {...}
  Next auto-update scheduled in [~15] minutes
  ```
- **Verify**: Auto-update triggers at the correct time (:01, :16, :31, or :46)
- **Verify**: Data refreshes automatically (timestamp updates)
- **Verify**: Next auto-update is scheduled ~15 minutes later

#### 2.6 Verify Continuous Cycle
- **Action**: Wait for the next auto-update (another 15 minutes)
- **Expected**: Auto-update triggers again at the next scheduled time
- **Expected**: Console shows "Auto-update triggered" message
- **Expected**: Cycle continues indefinitely (every 15 minutes)

#### 2.7 Test Page Reload (Reset Behavior)
- **Action**: Hard refresh the page again (Ctrl+Shift+R)
- **Expected**: 
  - "Auto-update waiting for initial data load to complete..." appears immediately
  - Auto-update waits for data to load again
  - After load completes, scheduling resumes

### ✅ Test Case #2 Success Criteria
- [ ] Auto-update does NOT start before initial data load
- [ ] Console shows "Auto-update waiting..." message during initial load
- [ ] Console shows "Next auto-update scheduled..." AFTER data loads
- [ ] Auto-update triggers at correct intervals (:01, :16, :31, :46 minutes)
- [ ] Auto-update cycle continues every ~15 minutes
- [ ] After page reload, behavior resets correctly (waits for load again)

---

## 🧪 Test Case #3: Integration Test (Both Fixes Together)

### Objective
Verify both fixes work together without conflicts.

### Steps to Test

#### 3.1 Load Application
- **Action**: Open browser with console (F12)
- **Action**: Load the application
- **Expected**: 
  - Auto-update waits for initial load (console message)
  - Data loads successfully
  - Auto-update schedules after load completes

#### 3.2 Apply Filters Before Auto-Update
- **Action**: Apply a column filter (e.g., ROE Min: 15)
- **Expected**: 
  - Filtered results show no null/"-" values
  - Wait for auto-update to trigger (~15 min)

#### 3.3 Verify Filter Persists After Auto-Update
- **Action**: Wait for auto-update to trigger (console will show "Auto-update triggered")
- **Expected**:
  - Data refreshes automatically
  - Filter is still applied (ROE Min: 15)
  - Filtered results STILL show no null/"-" values
  - Auto-update does not break the filter logic

#### 3.4 Change Filters After Auto-Update
- **Action**: Change to a different filter (e.g., PE Max: 25)
- **Expected**:
  - New filter works correctly
  - No null/"-" values in PE column
  - Auto-update continues in background (check console)

### ✅ Test Case #3 Success Criteria
- [ ] Auto-update and column filters work together without conflicts
- [ ] Filters persist correctly across auto-updates
- [ ] Null/"-" exclusion works before, during, and after auto-updates
- [ ] No errors in console during integration testing

---

## 📊 Quick Reference: Expected Behavior

| Scenario | Expected Behavior |
|----------|-------------------|
| **No filter applied** | All stocks visible (including null/"-" values) |
| **Numeric filter applied (min or max)** | Stocks with null/"-" values in that column are EXCLUDED |
| **Page load (before data)** | Auto-update waits (console: "waiting for initial data load") |
| **Page load (after data)** | Auto-update schedules (console: "Next auto-update scheduled") |
| **Auto-update timing** | Triggers at :01, :16, :31, :46 minutes of each hour |
| **Filter + Auto-update** | Filter logic persists correctly across auto-updates |

---

## 🐛 Troubleshooting

### Issue: Null/"-" values still showing after applying filter
**Solution**: 
- Verify the filter value is entered correctly (no extra spaces)
- Press Enter after entering the value
- Refresh the page and try again
- Check browser console for JavaScript errors

### Issue: Auto-update not triggering
**Solution**:
- Open console (F12) and check for error messages
- Verify initial data load completed (stocks table populated)
- Check if console shows "Next auto-update scheduled" message
- Wait for the correct time (:01, :16, :31, :46 minutes)
- Try refreshing the page

### Issue: Console not showing messages
**Solution**:
- Ensure Developer Tools are open (F12)
- Check Console tab is selected (not Network or Elements)
- Console might be cleared - refresh and watch from start
- Check console filter settings (should show "All levels")

---

## 📝 Test Results Template

Use this template to document your test results:

```
## Test Results - [Date]

### Test Case #1: Column Filters
- ✅/❌ Unfiltered view shows all stocks
- ✅/❌ ROE filter excludes null/"-" values
- ✅/❌ PE filter excludes null/"-" values
- ✅/❌ Market Cap range filter works correctly
- ✅/❌ Multiple filters work together
- ✅/❌ Clearing filters restores all stocks

**Notes**: 

### Test Case #2: Auto-Update
- ✅/❌ Auto-update waits for initial load
- ✅/❌ Console shows "waiting" message
- ✅/❌ Auto-update schedules after load
- ✅/❌ Triggers at correct time (:01, :16, :31, :46)
- ✅/❌ Continues every 15 minutes
- ✅/❌ Resets correctly on page reload

**Notes**:

### Test Case #3: Integration
- ✅/❌ Filters work before auto-update
- ✅/❌ Filters persist during auto-update
- ✅/❌ No conflicts between features
- ✅/❌ No console errors

**Notes**:

### Overall Status: ✅ PASS / ❌ FAIL

**Issues Found**:
1. 
2. 

**Recommendations**:
1. 
2. 
```

---

## ✅ Success Indicators

You'll know the fixes are working correctly when:

1. **Filter Fix**:
   - Applying any numeric filter immediately hides all stocks with null/"-" values in that column
   - Filter count decreases appropriately
   - Clearing filters shows all stocks again (including null values)

2. **Auto-Update Fix**:
   - Console shows "waiting" message during initial load
   - Auto-update only schedules AFTER data loads
   - Updates trigger every ~15 minutes at predictable times
   - No premature update attempts before data loads

3. **No Side Effects**:
   - No JavaScript errors in console
   - Application remains responsive
   - No performance degradation
   - Data displays correctly in all scenarios

---

**Last Updated**: December 30, 2025
**Test Version**: v2.2 (Bug Fixes)
