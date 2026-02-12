# UDTS Stock Screener

Real-time stock screening application for analyzing 500 NIFTY stocks using UDTS (Up-Down Trend System) methodology.

## Quick Start

### View Application
Open the preview URL in your browser to access the stock screener.

## New Features (December 2025)

### ✨ Sector Trend Analysis
- **Triple UDTS Score**: Calculates combined score from Monthly, Weekly, and Daily trends
  - Each timeframe: +100 for UP, -100 for DOWN
  - Sector score = MEDIAN of all stock scores in that sector
- **Real-time Display**: Shows top 5 UP trend sectors and top 5 DOWN trend sectors
- **Format**: "Sector Name / Score / Stock Count"
- **Position**: Left-aligned display next to filters

### 🎨 Redesigned Filter Layout
- **Compact Design**: Smaller filter buttons for better space utilization
- **Right-Aligned**: Filters positioned on the right side of the screen
- **6 Quick Filters**: 
  - UDTS Filter: All Stocks / ALL UDTS UP / ALL UDTS DOWN
  - Stock Type: All Stocks / NIFTY50 / Non-NIFTY50

## Features
- ✅ Multi-timeframe analysis (Monthly, Weekly, Daily, 1H, 15min)
- ✅ Real-time NIFTY 50 index tracking
- ✅ Fundamental data (ROE, PE, PB, DE, Revenue, Earnings)
- ✅ Institutional holdings tracking
- ✅ Advanced filtering and sorting (excludes null/blank values when filters applied)
- ✅ **Auto-refresh every 15 minutes** (starts only after first data load completes)
- ✅ **Batch parallel processing** (5 stocks simultaneously)
- ✅ **MongoDB persistent caching** (survives restarts)
- ✅ **Sector Trend Analysis** (Triple UDTS Score)

## Performance
- **First Load**: 8-12 minutes (fetching 500 stocks with batch parallel processing)
- **Subsequent Loads**: < 5 seconds (using MongoDB cache)
- **After Restart**: Fast recovery (data persisted in MongoDB)
- **Sector Trends**: Calculated with batch parallel processing
- **NO UNKNOWN VALUES**: Uses stale cache fallback to ensure complete data

## Controls
- **Refresh Button**: Clear cache and fetch fresh data
- **Refresh Stock List**: Update NIFTY 500 list from NSE
- **Filters**: 
  - UDTS Filter (All, ALL UP, ALL DOWN)
  - NIFTY50 Filter (All, NIFTY50, Non-NIFTY50)
  - Column Filters (Click "Show Column Filters")
- **Sector Trends**: View top 5 UP/DOWN trend sectors by Triple UDTS Score

## Sector Trend Calculation

### Triple UDTS Score (Per Stock)
```
Score = Monthly Score + Weekly Score + Daily Score
Where: UP = +100, DOWN = -100
Range: -300 (all DOWN) to +300 (all UP)
```

### Sector Triple UDTS Score
```
Sector Score = MEDIAN of all stock Triple UDTS Scores in that sector
```

### Display Format
```
UP Trend Sectors:
  Basic Materials / 100 / 27
  Energy / 100 / 9
  
DOWN Trend Sectors:
  Utilities / -100 / 9
  Consumer Defensive / -100 / 16
```

## Documentation
See `ARCHITECTURE.md` for detailed technical documentation.
See `IMPLEMENTATION_SUMMARY.md` for recent changes and implementation details.

## Technology
- Backend: FastAPI (Python) with Supabase caching & parallel processing
- Frontend: React with modern UI components
- Data Source: Yahoo Finance (yfinance)
- Database: Supabase PostgreSQL (cloud-based, free tier)

## Deployment
- **Backend**: Render.com (Free tier - 750 hours/month)
- **Frontend**: Vercel (Unlimited free for personal projects)
- **Database**: Supabase PostgreSQL (Free tier - 500MB storage)

For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## What's New in v2.2 (December 30, 2025)
- 🐛 **Fixed Column Filters**: Null/blank/"-" values now properly excluded when numeric filters applied
- 🐛 **Fixed Auto-Update**: Re-enabled 15-minute auto-refresh that starts ONLY after first data load completes
- ✅ **Smarter Filtering**: When ROE, PE, PB, or any numeric filter is active, stocks with missing data are automatically excluded
- ✅ **Intelligent Auto-Update**: Prevents premature updates during initial data population (8-12 minutes)

## What's New in v2.1 (December 2025)
- ✨ **Sector Trend Analysis**: Real-time sector trends based on Triple UDTS Score
- ✨ **Redesigned Filters**: Compact, right-aligned filter layout
- ✨ **Side-by-Side Display**: Sector trends on left, filters on right
- ✨ **Updated URLs**: Frontend and backend URLs synchronized

## Previous Updates (v2.0)
- ✨ **Parallel Processing**: 15x faster initial load (3-5 min vs 11+ min)
- ✨ **MongoDB Caching**: Data persists across restarts
- ✨ **Optimized Deployment**: Removed 30+ unused files (88MB saved)

**Last Updated**: December 30, 2025 (v2.2 - Bug Fixes)
