# Sorting Logic Updates - December 30, 2025

## Summary
Updated sorting logic for CMP column and sector/industry DOWN trend details as requested.

## Changes Made

### 1. CMP Column Sorting Logic (Frontend)

**File**: `/app/frontend/src/App.js`

**Change Location**: Line 569-570

**Before**:
```javascript
case "cmp":
  return stock.cmp;
```

**After**:
```javascript
case "cmp":
  return stock.cmp_change_pct;
```

**Impact**: 
- When users click the CMP column header to sort, it now sorts by the **percentage change** (the small font second-line text in each cell)
- Previous behavior: Sorted by absolute CMP value
- New behavior: Sorted by % change from yesterday's close

---

### 2. Sector/Industry DOWN Trend Details Sorting

**File**: `/app/frontend/src/App.js`

#### A. Updated `getStocksForSector` Function (Line 422)

**Before**:
```javascript
const getStocksForSector = (sectorName) => {
  // Always sorted descending by tripleScore
}
```

**After**:
```javascript
const getStocksForSector = (sectorName, isDownTrend = false) => {
  // Conditional sorting based on UP/DOWN trend
  if (isDownTrend) {
    // Sort ASCENDING by tripleScore, then ASCENDING by upside %
  } else {
    // Original logic for UP trends (descending)
  }
}
```

**Sorting Logic for DOWN Trends**:
```javascript
if (isDownTrend) {
  // Primary: Triple UDTS Score ASCENDING (lowest first: -300, -200, -100, 0, 100, 200, 300)
  if (a.tripleScore !== b.tripleScore) {
    return a.tripleScore - b.tripleScore; // Ascending
  }
  // Secondary: Upside % ASCENDING (lowest first: -50%, -20%, 0%, 10%, 50%)
  return a.upsidePct - b.upsidePct; // Ascending
}
```

#### B. Updated `getStocksForIndustry` Function (Line 489)

Same logic applied for industry trends:
- Added `isDownTrend` parameter
- Conditional sorting: ascending for DOWN trends, descending for UP trends

#### C. Updated Function Calls

**Sector Modal - DOWN Trends** (Line 1195):
```javascript
// Before:
const sectorStocks = getStocksForSector(trend.sector);

// After:
const sectorStocks = getStocksForSector(trend.sector, true);
```

**Industry Modal - DOWN Trends** (Line 1374):
```javascript
// Before:
const industryStocks = getStocksForIndustry(trend.industry);

// After:
const industryStocks = getStocksForIndustry(trend.industry, true);
```

**UP Trends remain unchanged** (pass no second parameter, defaults to `false`):
```javascript
const sectorStocks = getStocksForSector(trend.sector);
const industryStocks = getStocksForIndustry(trend.industry);
```

---

## Behavior Summary

### CMP Column Sorting
| User Action | Previous Behavior | New Behavior |
|------------|------------------|--------------|
| Click CMP header (1st time) | Sort DESC by CMP value | Sort DESC by % change |
| Click CMP header (2nd time) | Sort ASC by CMP value | Sort ASC by % change |

**Example**:
- Stock A: CMP = 1500, Change = +5.2%
- Stock B: CMP = 2000, Change = -2.3%
- Stock C: CMP = 800, Change = +8.1%

**Before**: B (2000) → A (1500) → C (800)  
**After**: C (+8.1%) → A (+5.2%) → B (-2.3%)

---

### Sector/Industry Details - DOWN Trends

| Aspect | UP Trends | DOWN Trends (NEW) |
|--------|-----------|------------------|
| Primary Sort | Triple UDTS Score DESC | Triple UDTS Score ASC |
| Secondary Sort | Fully UP/DOWN priority | N/A (removed) |
| Tertiary Sort | Upside % DESC | Upside % ASC |

**Example for DOWN Trend Sector**:

**Stock Data**:
- Stock A: Triple Score = -300, Upside = -10%
- Stock B: Triple Score = -200, Upside = 5%
- Stock C: Triple Score = -300, Upside = -5%
- Stock D: Triple Score = 0, Upside = 15%

**Before** (DESC by score, then DESC by upside):
D (0, 15%) → B (-200, 5%) → C (-300, -5%) → A (-300, -10%)

**After** (ASC by score, then ASC by upside):
A (-300, -10%) → C (-300, -5%) → B (-200, 5%) → D (0, 15%)

**Rationale**: 
- Shows most bearish stocks first (lowest Triple UDTS Score)
- Within same score, shows stocks with lowest upside first (most potential downside)

---

## UP Trends - Unchanged

For UP trend sectors/industries, the original sorting logic remains:
1. **Primary**: Triple UDTS Score DESCENDING (highest first)
2. **Secondary**: Fully UP stocks prioritized
3. **Tertiary**: Upside % DESCENDING (highest first)

This shows the most bullish stocks first with the highest potential upside.

---

## Testing Instructions

### 1. Test CMP Column Sorting
1. Load the stock screener
2. Click the "CMP" column header
3. Verify stocks are sorted by the % change (small text) in descending order
4. Click again to reverse (ascending order by % change)

### 2. Test Sector DOWN Trend Details
1. Load the stock screener
2. Click "SECTOR TRENDS" button
3. Scroll to "DETAILS" section
4. Find a DOWN trend sector (e.g., "Utilities (DOWN Trend)")
5. Verify stocks are sorted:
   - First by Triple UDTS Score ascending (-300, -200, -100, etc.)
   - Then by Upside % ascending within same score

### 3. Test Industry DOWN Trend Details
1. Load the stock screener
2. Click "INDUSTRY TRENDS" button
3. Scroll to "DETAILS" section
4. Find a DOWN trend industry
5. Verify same ascending sort logic as sectors

### 4. Verify UP Trends Still Work
1. Check UP trend sectors/industries in DETAILS
2. Verify they still sort descending (highest scores first)

---

## Technical Details

### Triple UDTS Score Calculation
```javascript
Monthly: UP = +100, DOWN = -100, UNKNOWN = 0
Weekly: UP = +100, DOWN = -100, UNKNOWN = 0
Daily: UP = +100, DOWN = -100, UNKNOWN = 0

Triple Score = Monthly + Weekly + Daily
Range: -300 (all DOWN) to +300 (all UP)
```

### Upside % Calculation
- Positive values: Stock price has room to grow
- Negative values: Stock price may decline further
- Calculated based on analyst targets and technical levels

---

## Files Modified

1. **Frontend**: `/app/frontend/src/App.js`
   - Line 569-570: CMP sorting value changed
   - Line 422-477: `getStocksForSector` function updated
   - Line 489-534: `getStocksForIndustry` function updated
   - Line 1195: Sector DOWN trend function call updated
   - Line 1374: Industry DOWN trend function call updated

---

## Rollback Instructions

If issues occur, revert these specific changes:

### Rollback CMP Sorting:
```javascript
// Change line 570 from:
return stock.cmp_change_pct;
// Back to:
return stock.cmp;
```

### Rollback DOWN Trend Sorting:
1. Remove `isDownTrend` parameter from both functions
2. Remove conditional sorting logic
3. Change function calls back to single parameter
4. Restart frontend: `sudo supervisorctl restart frontend`

---

**Last Updated**: December 30, 2025  
**Status**: ✅ Implementation Complete  
**Frontend Restart**: Required and completed  
**Testing**: Ready for user validation
