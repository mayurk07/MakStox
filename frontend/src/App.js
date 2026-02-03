import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import * as Collapsible from "@radix-ui/react-collapsible";
import "./App.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// NIFTY 50 constituents list - Updated from NSE CSV (DUMMYHDLVR removed)
const NIFTY50_SYMBOLS = [
  "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV",
  "BEL", "BHARTIARTL", "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "ETERNAL", "GRASIM",
  "HCLTECH", "HDFCBANK", "HDFCLIFE", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC", "INFY",
  "INDIGO", "JSWSTEEL", "JIOFIN", "KOTAKBANK", "LT", "M&M", "MARUTI", "MAXHEALTH",
  "NTPC", "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN", "SBIN",
  "SUNPHARMA", "TCS", "TATACONSUM", "TMPV", "TATASTEEL", "TECHM", "TITAN", "TRENT",
  "ULTRACEMCO", "WIPRO"
];

function App() {
  const [stocks, setStocks] = useState([]);
  const [nifty50, setNifty50] = useState(null);
  const [sectorTrends, setSectorTrends] = useState({ up_trends: [], down_trends: [] });
  const [industryTrends, setIndustryTrends] = useState({ up_trends: [], down_trends: [] });
  const [loadingSectors, setLoadingSectors] = useState(false);
  const [loadingIndustries, setLoadingIndustries] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [filter, setFilter] = useState("all");
  const [niftyFilter, setNiftyFilter] = useState("all");
  const [loadingTime, setLoadingTime] = useState(0);
  const [refreshingList, setRefreshingList] = useState(false);
  const [listRefreshMessage, setListRefreshMessage] = useState("");
  const [showSectorModal, setShowSectorModal] = useState(false);
  const [showIndustryModal, setShowIndustryModal] = useState(false);
  const [initialDataLoaded, setInitialDataLoaded] = useState(false); // Track if first data load is complete
  const [isHeaderOpen, setIsHeaderOpen] = useState(true); // Header section expanded by default
  const [isFiltersOpen, setIsFiltersOpen] = useState(true); // Filters section expanded by default
  const [displayLimit, setDisplayLimit] = useState(100); // Initially show 100 rows for faster rendering
  
  // Column filters state
  const [columnFilters, setColumnFilters] = useState({
    sector: "",
    industry: "",
    monthly_trend: "all",
    weekly_trend: "all",
    daily_trend: "all",
    cmp_change_min: "",
    cmp_change_max: "",
    dist_min: "",
    dist_max: "",
    score_min: "",
    score_max: "",
    upside_min: "",
    upside_max: "",
    two_yr_high_min: "",
    two_yr_high_max: "",
    inst_hold_min: "",
    inst_hold_max: "",
    mcap_min: "",
    mcap_max: "",
    roe_min: "",
    roe_max: "",
    pe_min: "",
    pe_max: "",
    pb_min: "",
    pb_max: "",
    de_min: "",
    de_max: "",
    rev_min: "",
    rev_max: "",
    earn_min: "",
    earn_max: "",
    div_yield_min: "",
    div_yield_max: "",
    net_income_min: "",
    net_income_max: "",
    ent_ebitda_min: "",
    ent_ebitda_max: "",
    ent_rev_min: "",
    ent_rev_max: "",
    daily_rsi_min: "",
    daily_rsi_max: "",
    daily_adx_min: "",
    daily_adx_max: "",
    daily_supertrend: "all",
    daily_bb_pct_min: "",
    daily_bb_pct_max: "",
    weekly_bb_pct_min: "",
    weekly_bb_pct_max: "",
    monthly_bb_pct_min: "",
    monthly_bb_pct_max: ""
  });
  const [showFilters, setShowFilters] = useState(false);
  
  // Sorting state
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("desc"); // "asc" or "desc"

  const fetchData = useCallback(async () => {
    setLoading(true);
    setLoadingTime(0);
    try {
      // Add cache-busting parameter to force fresh data
      const cacheBuster = Date.now();
      const [stocksRes, niftyRes] = await Promise.all([
        axios.get(`${API}/stocks?_=${cacheBuster}`, { 
          timeout: 86400000, // 24 hour timeout (1440 minutes) - let backend take as long as needed, no timeout issues
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        }),
        axios.get(`${API}/nifty50?_=${cacheBuster}`, { 
          timeout: 3600000, // 1 hour timeout for NIFTY 50 (very generous)
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        })
      ]);
      
      console.log("Stocks response:", stocksRes.data);
      setStocks(stocksRes.data.stocks || []);
      setLastUpdated(stocksRes.data.timestamp);
      setNifty50(niftyRes.data);
      setInitialDataLoaded(true); // Mark initial data as loaded
    } catch (e) {
      console.error("Error fetching data:", e);
      console.error("Error details:", e.message, e.response);
      // Show error message but don't clear existing data if timeout occurs
      if (e.code === 'ECONNABORTED' || e.message.includes('timeout')) {
        console.error("Request timed out - stock data is still loading on backend");
        alert("The request timed out, but stock data may still be loading. Please wait and try refreshing in a few minutes.");
      } else if (e.response) {
        alert(`Error loading stock data: ${e.response.status} - ${e.response.statusText}`);
      } else if (e.request) {
        alert("Network error: Unable to reach the server. Please check your connection and try again.");
      }
    }
    setLoading(false);
  }, []);

  const handleRefresh = async () => {
    try {
      const cacheBuster = Date.now();
      await axios.get(`${API}/refresh?_=${cacheBuster}`, { 
        timeout: 3600000,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      }); // 1 hour timeout for refresh (very generous)
      fetchData();
    } catch (e) {
      console.error("Error refreshing:", e);
      // Even if refresh endpoint fails, try fetching data
      fetchData();
    }
  };

  const handleRefreshStockList = async () => {
    setRefreshingList(true);
    setListRefreshMessage("Fetching stock list from NSE...");
    try {
      const cacheBuster = Date.now();
      const response = await axios.get(`${API}/refresh_stock_list?_=${cacheBuster}`, { 
        timeout: 120000, // 2 minute timeout
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      if (response.data.success) {
        if (response.data.list_changed) {
          setListRefreshMessage(`✓ Stock list updated! ${response.data.stock_count} stocks. Cache cleared. Click "Refresh" to reload data.`);
        } else {
          setListRefreshMessage(`✓ Stock list unchanged. ${response.data.stock_count} stocks.`);
        }
      } else {
        setListRefreshMessage(`⚠ ${response.data.message}`);
      }
      
      // Auto-clear message after 10 seconds
      setTimeout(() => setListRefreshMessage(""), 10000);
    } catch (e) {
      console.error("Error refreshing stock list:", e);
      setListRefreshMessage(`✗ Error: ${e.message}`);
      setTimeout(() => setListRefreshMessage(""), 10000);
    }
    setRefreshingList(false);
  };

  const handleOpenSectorAnalysis = async () => {
    setLoadingSectors(true);
    setShowSectorModal(true);
    
    try {
      const cacheBuster = Date.now();
      const response = await axios.get(`${API}/sector-trends?_=${cacheBuster}`, { 
        timeout: 86400000,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log("Sector trends response:", response.data);
      setSectorTrends({
        up_trends: response.data.up_trends || [],
        down_trends: response.data.down_trends || []
      });
      setLoadingSectors(false);
    } catch (e) {
      console.error("Error fetching sector trends:", e);
      setSectorTrends({ up_trends: [], down_trends: [] });
      setLoadingSectors(false);
    }
  };

  const handleOpenIndustryAnalysis = async () => {
    setLoadingIndustries(true);
    setShowIndustryModal(true);
    
    try {
      const cacheBuster = Date.now();
      const response = await axios.get(`${API}/industry-trends?_=${cacheBuster}`, { 
        timeout: 86400000,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log("Industry trends response:", response.data);
      setIndustryTrends({
        up_trends: response.data.up_trends || [],
        down_trends: response.data.down_trends || []
      });
      setLoadingIndustries(false);
    } catch (e) {
      console.error("Error fetching industry trends:", e);
      setIndustryTrends({ up_trends: [], down_trends: [] });
      setLoadingIndustries(false);
    }
  };

  // Preset Filter Handlers
  const handleBestUUFilter = () => {
    // Reset all filters first
    setFilter("all");
    setNiftyFilter("all");
    setSortColumn(null);
    setSortDirection("desc");
    
    // Apply BEST UU preset filters
    setColumnFilters({
      sector: "",
      industry: "",
      monthly_trend: "UP",
      weekly_trend: "UP",
      daily_trend: "all",
      cmp_change_min: "",
      cmp_change_max: "",
      dist_min: "",
      dist_max: "",
      score_min: "",
      score_max: "",
      upside_min: "",
      upside_max: "",
      two_yr_high_min: "15",
      two_yr_high_max: "",
      inst_hold_min: "",
      inst_hold_max: "",
      mcap_min: "20",
      mcap_max: "",
      roe_min: "15",
      roe_max: "",
      pe_min: "",
      pe_max: "50",
      pb_min: "",
      pb_max: "",
      de_min: "",
      de_max: "50",
      rev_min: "0",
      rev_max: "",
      earn_min: "0",
      earn_max: "",
      div_yield_min: "",
      div_yield_max: "",
      net_income_min: "50",
      net_income_max: "",
      ent_ebitda_min: "",
      ent_ebitda_max: "",
      ent_rev_min: "",
      ent_rev_max: "",
      daily_rsi_min: "",
      daily_rsi_max: "",
      daily_adx_min: "",
      daily_adx_max: "",
      daily_supertrend: "all",
      daily_bb_pct_min: "",
      daily_bb_pct_max: "",
      weekly_bb_pct_min: "",
      weekly_bb_pct_max: "",
      monthly_bb_pct_min: "",
      monthly_bb_pct_max: ""
    });
  };

  const handleBestTurnFilter = () => {
    // Reset all filters first
    setFilter("all");
    setNiftyFilter("all");
    setSortColumn(null);
    setSortDirection("desc");
    
    // Apply BEST Turn preset filters
    setColumnFilters({
      sector: "",
      industry: "",
      monthly_trend: "DOWN",
      weekly_trend: "UP",
      daily_trend: "UP",
      cmp_change_min: "",
      cmp_change_max: "",
      dist_min: "",
      dist_max: "",
      score_min: "",
      score_max: "",
      upside_min: "",
      upside_max: "",
      two_yr_high_min: "15",
      two_yr_high_max: "",
      inst_hold_min: "",
      inst_hold_max: "",
      mcap_min: "20",
      mcap_max: "",
      roe_min: "15",
      roe_max: "",
      pe_min: "",
      pe_max: "50",
      pb_min: "",
      pb_max: "",
      de_min: "",
      de_max: "50",
      rev_min: "0",
      rev_max: "",
      earn_min: "0",
      earn_max: "",
      div_yield_min: "",
      div_yield_max: "",
      net_income_min: "50",
      net_income_max: "",
      ent_ebitda_min: "",
      ent_ebitda_max: "",
      ent_rev_min: "",
      ent_rev_max: "",
      daily_rsi_min: "",
      daily_rsi_max: "",
      daily_adx_min: "",
      daily_adx_max: "",
      daily_supertrend: "all",
      daily_bb_pct_min: "",
      daily_bb_pct_max: "",
      weekly_bb_pct_min: "",
      weekly_bb_pct_max: "",
      monthly_bb_pct_min: "",
      monthly_bb_pct_max: ""
    });
  };


  useEffect(() => {
    fetchData();
    
    // Auto-update every 15 minutes - ONLY after initial data is loaded
    let timeoutId;
    
    // Calculate next update time at :00, :15, :30, or :45 minutes
    const getNextUpdateTime = () => {
      const now = new Date();
      const currentMinutes = now.getMinutes();
      const currentSeconds = now.getSeconds();
      const currentMilliseconds = now.getMilliseconds();
      
      // Target minutes: 0, 15, 30, 45
      const targetMinutes = [0, 15, 30, 45];
      
      // Find the next target minute
      let nextMinute = targetMinutes.find(m => m > currentMinutes);
      
      // If no target found in current hour, use first target of next hour
      if (!nextMinute) {
        nextMinute = targetMinutes[0] + 60; // Add 60 to move to next hour
      }
      
      // Calculate milliseconds to next target time (exactly at :00 seconds)
      const minutesToNext = nextMinute - currentMinutes;
      const msToNext = (minutesToNext * 60 - currentSeconds) * 1000 - currentMilliseconds;
      
      return msToNext;
    };
    
    const scheduleNextUpdate = () => {
      // Only schedule auto-update if initial data has been loaded
      if (!initialDataLoaded) {
        console.log("Auto-update waiting for initial data load to complete...");
        return;
      }
      
      const msToNext = getNextUpdateTime();
      const nextUpdateTime = new Date(Date.now() + msToNext);
      console.log(`Next auto-update scheduled at ${nextUpdateTime.toLocaleTimeString()} (in ${Math.round(msToNext / 1000 / 60)} minutes)`);
      
      timeoutId = setTimeout(() => {
        console.log("Auto-update triggered at", new Date().toLocaleTimeString());
        fetchData();
        scheduleNextUpdate(); // Schedule the next update recursively
      }, msToNext);
    };
    
    // Start scheduling only after initial data is loaded
    if (initialDataLoaded) {
      scheduleNextUpdate();
    }
    
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [fetchData, initialDataLoaded]);

  // Timer to track loading time
  useEffect(() => {
    let intervalId;
    if (loading) {
      intervalId = setInterval(() => {
        setLoadingTime(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [loading]);

  // Helper function to check if stock is ALL UP
  const isAllUp = (s) => {
    return s.udts?.monthly === "UP" && 
           s.udts?.weekly === "UP" && 
           s.udts?.daily === "UP" && 
           s.udts?.["1hour"] === "UP" && 
           s.udts?.["15min"] === "UP" &&
           s.biggest_trend?.direction === "UP" &&
           s.initial_trend?.direction === "UP" &&
           s.cmp_label === "YES";
  };

  // Helper function to check if stock is ALL DOWN
  const isAllDown = (s) => {
    return s.udts?.monthly === "DOWN" && 
           s.udts?.weekly === "DOWN" && 
           s.udts?.daily === "DOWN" && 
           s.udts?.["1hour"] === "DOWN" && 
           s.udts?.["15min"] === "DOWN" &&
           s.biggest_trend?.direction === "DOWN" &&
           s.initial_trend?.direction === "DOWN" &&
           s.cmp_label === "YES";
  };

  // Helper function for numeric range filtering
  const isInRange = (value, min, max) => {
    const hasMin = min !== "" && !isNaN(parseFloat(min));
    const hasMax = max !== "" && !isNaN(parseFloat(max));
    
    // If any filter is applied (min or max), exclude null/undefined/NaN/"-" values
    if (hasMin || hasMax) {
      if (value === null || value === undefined || value === "" || value === "-") return false;
      const numValue = parseFloat(value);
      if (isNaN(numValue)) return false;
      
      if (hasMin && hasMax) {
        return numValue >= parseFloat(min) && numValue <= parseFloat(max);
      } else if (hasMin) {
        return numValue >= parseFloat(min);
      } else if (hasMax) {
        return numValue <= parseFloat(max);
      }
    }
    
    // If no filter is applied, include all values (including null/undefined)
    return true;
  };

  const filteredStocks = stocks.filter(s => {
    // Apply UDTS filter
    if (filter === "all_up" && !isAllUp(s)) return false;
    if (filter === "all_down" && !isAllDown(s)) return false;
    
    // Apply NIFTY50 filter
    if (niftyFilter === "nifty50" && !NIFTY50_SYMBOLS.includes(s.symbol)) return false;
    if (niftyFilter === "non_nifty50" && NIFTY50_SYMBOLS.includes(s.symbol)) return false;
    
    // Apply column filters
    // Text filters
    if (columnFilters.sector && s.sector && !s.sector.toLowerCase().includes(columnFilters.sector.toLowerCase())) return false;
    if (columnFilters.industry && s.industry && !s.industry.toLowerCase().includes(columnFilters.industry.toLowerCase())) return false;
    
    // Trend direction filters (M, W, D)
    if (columnFilters.monthly_trend !== "all" && s.udts?.monthly !== columnFilters.monthly_trend) return false;
    if (columnFilters.weekly_trend !== "all" && s.udts?.weekly !== columnFilters.weekly_trend) return false;
    if (columnFilters.daily_trend !== "all" && s.udts?.daily !== columnFilters.daily_trend) return false;
    
    // CMP % change filter
    if (!isInRange(s.cmp_change_pct, columnFilters.cmp_change_min, columnFilters.cmp_change_max)) return false;
    
    // Dist% filter
    if (!isInRange(s.max_distance, columnFilters.dist_min, columnFilters.dist_max)) return false;
    
    // Score filter
    if (!isInRange(s.scores?.total, columnFilters.score_min, columnFilters.score_max)) return false;
    
    // Upside% filter
    if (!isInRange(s.upside, columnFilters.upside_min, columnFilters.upside_max)) return false;
    
    // 2yr high % filter
    if (!isInRange(s.two_yr_high_pct, columnFilters.two_yr_high_min, columnFilters.two_yr_high_max)) return false;
    
    // Inst. Hold% filter (institutional holding percentage - can be string "NA" or numeric)
    const instValue = s.inst_holding_pct;
    if (instValue && instValue !== "NA") {
      const numInst = parseFloat(instValue);
      if (!isNaN(numInst) && !isInRange(numInst, columnFilters.inst_hold_min, columnFilters.inst_hold_max)) return false;
    }
    
    // Market Cap filter
    if (!isInRange(s.market_cap_tkc, columnFilters.mcap_min, columnFilters.mcap_max)) return false;
    
    // ROE filter
    if (!isInRange(s.fundamentals?.roe, columnFilters.roe_min, columnFilters.roe_max)) return false;
    
    // PE filter
    if (!isInRange(s.fundamentals?.pe, columnFilters.pe_min, columnFilters.pe_max)) return false;
    
    // PB filter
    if (!isInRange(s.fundamentals?.pb, columnFilters.pb_min, columnFilters.pb_max)) return false;
    
    // DE filter
    if (!isInRange(s.fundamentals?.de, columnFilters.de_min, columnFilters.de_max)) return false;
    
    // Revenue% filter
    if (!isInRange(s.fundamentals?.revenue_growth, columnFilters.rev_min, columnFilters.rev_max)) return false;
    
    // Earnings% filter
    if (!isInRange(s.fundamentals?.earnings_growth, columnFilters.earn_min, columnFilters.earn_max)) return false;
    
    // Dividend Yield% filter
    if (!isInRange(s.fundamentals?.dividend_yield, columnFilters.div_yield_min, columnFilters.div_yield_max)) return false;
    
    // Net Income to Common filter
    if (!isInRange(s.fundamentals?.net_income_to_common, columnFilters.net_income_min, columnFilters.net_income_max)) return false;
    
    // Enterprise to EBITDA filter
    if (!isInRange(s.fundamentals?.enterprise_to_ebitda, columnFilters.ent_ebitda_min, columnFilters.ent_ebitda_max)) return false;
    
    // Enterprise to Revenue filter
    if (!isInRange(s.fundamentals?.enterprise_to_revenue, columnFilters.ent_rev_min, columnFilters.ent_rev_max)) return false;
    
    // Daily RSI filter
    if (!isInRange(s.daily_rsi, columnFilters.daily_rsi_min, columnFilters.daily_rsi_max)) return false;
    
    // Daily ADX filter
    if (!isInRange(s.daily_adx, columnFilters.daily_adx_min, columnFilters.daily_adx_max)) return false;
    
    // Daily Supertrend filter (direction only)
    if (columnFilters.daily_supertrend !== "all" && s.daily_supertrend?.direction !== columnFilters.daily_supertrend) return false;
    
    // Daily %BB filter
    if (!isInRange(s.daily_bb_pct, columnFilters.daily_bb_pct_min, columnFilters.daily_bb_pct_max)) return false;
    
    // Weekly %BB filter
    if (!isInRange(s.weekly_bb_pct, columnFilters.weekly_bb_pct_min, columnFilters.weekly_bb_pct_max)) return false;
    
    // Monthly %BB filter
    if (!isInRange(s.monthly_bb_pct, columnFilters.monthly_bb_pct_min, columnFilters.monthly_bb_pct_max)) return false;
    
    return true;
  });

  const isTriple = (s) => s.is_triple_up || s.is_triple_down;

  // Get stocks for a specific sector with Triple UDTS Score sorting
  const getStocksForSector = (sectorName, isDownTrend = false) => {
    return stocks
      .filter(s => s.sector === sectorName)
      .map(s => {
        // Calculate Triple UDTS Score (M + W + D)
        const monthlyTrend = s.udts?.monthly;
        const weeklyTrend = s.udts?.weekly;
        const dailyTrend = s.udts?.daily;
        
        const monthly = monthlyTrend === "UP" ? 100 : monthlyTrend === "DOWN" ? -100 : 0;
        const weekly = weeklyTrend === "UP" ? 100 : weeklyTrend === "DOWN" ? -100 : 0;
        const daily = dailyTrend === "UP" ? 100 : dailyTrend === "DOWN" ? -100 : 0;
        const tripleScore = monthly + weekly + daily;
        
        // Check if fully UP or fully DOWN
        const isFullyUp = monthlyTrend === "UP" && weeklyTrend === "UP" && dailyTrend === "UP";
        const isFullyDown = monthlyTrend === "DOWN" && weeklyTrend === "DOWN" && dailyTrend === "DOWN";
        
        return {
          ...s,
          tripleScore,
          monthlyTrend: monthlyTrend || "-",
          weeklyTrend: weeklyTrend || "-",
          dailyTrend: dailyTrend || "-",
          upsidePct: s.upside || 0,
          isFullyUp,
          isFullyDown,
          dividendYield: s.fundamentals?.dividend_yield,
          evToEbitda: s.fundamentals?.enterprise_to_ebitda,
          evToRevenue: s.fundamentals?.enterprise_to_revenue
        };
      })
      .sort((a, b) => {
        if (isDownTrend) {
          // For DOWN trend sectors: sort ascending by tripleScore, then ascending by upside %
          if (a.tripleScore !== b.tripleScore) {
            return a.tripleScore - b.tripleScore; // Ascending
          }
          // Tertiary: Upside % ascending
          return a.upsidePct - b.upsidePct; // Ascending
        } else {
          // For UP trend sectors: original logic (descending)
          // Primary: Triple UDTS Score descending
          if (a.tripleScore !== b.tripleScore) {
            return b.tripleScore - a.tripleScore;
          }
          // Secondary: For UP sectors, prioritize fully UP stocks; for DOWN sectors, prioritize fully DOWN stocks
          // If scores are equal, sort by fully UP/DOWN status
          if (a.isFullyUp !== b.isFullyUp) {
            return b.isFullyUp - a.isFullyUp;
          }
          if (a.isFullyDown !== b.isFullyDown) {
            return b.isFullyDown - a.isFullyDown;
          }
          // Tertiary: Upside % descending
          return b.upsidePct - a.upsidePct;
        }
      });
  };

  // Get stocks for a specific industry with Triple UDTS Score sorting
  const getStocksForIndustry = (industryName, isDownTrend = false) => {
    return stocks
      .filter(s => s.industry === industryName)
      .map(s => {
        // Calculate Triple UDTS Score (M + W + D)
        const monthlyTrend = s.udts?.monthly;
        const weeklyTrend = s.udts?.weekly;
        const dailyTrend = s.udts?.daily;
        
        const monthly = monthlyTrend === "UP" ? 100 : monthlyTrend === "DOWN" ? -100 : 0;
        const weekly = weeklyTrend === "UP" ? 100 : weeklyTrend === "DOWN" ? -100 : 0;
        const daily = dailyTrend === "UP" ? 100 : dailyTrend === "DOWN" ? -100 : 0;
        const tripleScore = monthly + weekly + daily;
        
        // Check if fully UP or fully DOWN
        const isFullyUp = monthlyTrend === "UP" && weeklyTrend === "UP" && dailyTrend === "UP";
        const isFullyDown = monthlyTrend === "DOWN" && weeklyTrend === "DOWN" && dailyTrend === "DOWN";
        
        return {
          ...s,
          tripleScore,
          monthlyTrend: monthlyTrend || "-",
          weeklyTrend: weeklyTrend || "-",
          dailyTrend: dailyTrend || "-",
          upsidePct: s.upside || 0,
          isFullyUp,
          isFullyDown,
          dividendYield: s.fundamentals?.dividend_yield,
          evToEbitda: s.fundamentals?.enterprise_to_ebitda,
          evToRevenue: s.fundamentals?.enterprise_to_revenue
        };
      })
      .sort((a, b) => {
        if (isDownTrend) {
          // For DOWN trend industries: sort ascending by tripleScore, then ascending by upside %
          if (a.tripleScore !== b.tripleScore) {
            return a.tripleScore - b.tripleScore; // Ascending
          }
          // Tertiary: Upside % ascending
          return a.upsidePct - b.upsidePct; // Ascending
        } else {
          // For UP trend industries: original logic (descending)
          // Primary: Triple UDTS Score descending
          if (a.tripleScore !== b.tripleScore) {
            return b.tripleScore - a.tripleScore;
          }
          // Secondary: For UP industries, prioritize fully UP stocks; for DOWN industries, prioritize fully DOWN stocks
          // If scores are equal, sort by fully UP/DOWN status
          if (a.isFullyUp !== b.isFullyUp) {
            return b.isFullyUp - a.isFullyUp;
          }
          if (a.isFullyDown !== b.isFullyDown) {
            return b.isFullyDown - a.isFullyDown;
          }
          // Tertiary: Upside % descending
          return b.upsidePct - a.upsidePct;
        }
      });
  };

  // Column header click handler for sorting
  const handleColumnSort = (columnName) => {
    if (sortColumn === columnName) {
      // Toggle direction if same column
      setSortDirection(sortDirection === "desc" ? "asc" : "desc");
    } else {
      // New column, default to descending
      setSortColumn(columnName);
      setSortDirection("desc");
    }
  };

  // Helper function to extract value for sorting based on column type
  const getSortValue = (stock, column) => {
    switch (column) {
      case "symbol":
        return stock.symbol || "";
      case "sector":
        return stock.sector || "";
      case "industry":
        return stock.industry || "";
      case "monthly":
        return stock.support_distances?.monthly;
      case "weekly":
        return stock.support_distances?.weekly;
      case "daily":
        return stock.support_distances?.daily;
      case "hourly":
        return stock.support_distances?.["1hour"];
      case "min15":
        return stock.support_distances?.["15min"];
      case "cmp":
        return stock.cmp_change_pct;
      case "big_trend":
        return stock.biggest_trend?.distance_pct;
      case "init_trend":
        return stock.initial_trend?.direction || "";
      case "dist":
        return stock.max_distance;
      case "score":
        return stock.scores?.total;
      case "upside":
        return stock.upside;
      case "two_yr_high":
        return stock.two_yr_high_pct;
      case "inst_hold":
        const instValue = stock.inst_holding_pct;
        if (instValue && instValue !== "NA") {
          const numInst = parseFloat(instValue);
          return isNaN(numInst) ? null : numInst;
        }
        return null;
      case "mcap":
        return stock.market_cap_tkc;
      case "roe":
        return stock.fundamentals?.roe;
      case "pe":
        return stock.fundamentals?.pe;
      case "pb":
        return stock.fundamentals?.pb;
      case "de":
        return stock.fundamentals?.de;
      case "rev":
        return stock.fundamentals?.revenue_growth;
      case "earn":
        return stock.fundamentals?.earnings_growth;
      case "div_yield":
        return stock.fundamentals?.dividend_yield;
      case "net_income":
        return stock.fundamentals?.net_income_to_common;
      case "ent_ebitda":
        return stock.fundamentals?.enterprise_to_ebitda;
      case "ent_rev":
        return stock.fundamentals?.enterprise_to_revenue;
      case "daily_rsi":
        return stock.daily_rsi;
      case "daily_adx":
        return stock.daily_adx;
      case "daily_supertrend":
        return stock.daily_supertrend?.level;
      case "daily_bb_pct":
        return stock.daily_bb_pct;
      case "weekly_bb_pct":
        return stock.weekly_bb_pct;
      case "monthly_bb_pct":
        return stock.monthly_bb_pct;
      default:
        return null;
    }
  };

  // Check if value is null/blank/NA/-
  const isNullValue = (value) => {
    return value === null || value === undefined || value === "" || value === "-" || value === "NA";
  };

  // Apply conditional sorting based on filter OR user-selected column
  const sortedFilteredStocks = [...filteredStocks].sort((a, b) => {
    // If user has selected a column to sort by, use that
    if (sortColumn) {
      // Special handling for SCORE column - with secondary sorting by Up%
      if (sortColumn === "score") {
        const scoreA = a.scores?.total;
        const scoreB = b.scores?.total;
        const upsideA = a.upside;
        const upsideB = b.upside;
        
        // Check for null values in score
        const isNullA = scoreA === null || scoreA === undefined;
        const isNullB = scoreB === null || scoreB === undefined;
        
        // Always put null score values at the bottom
        if (isNullA && !isNullB) return 1;
        if (!isNullA && isNullB) return -1;
        if (isNullA && isNullB) return 0;
        
        // Primary sorting: by score (desc or asc based on sortDirection)
        if (scoreA !== scoreB) {
          return sortDirection === "desc" ? scoreB - scoreA : scoreA - scoreB;
        }
        
        // Secondary sorting: by upside % in the SAME direction as score
        // Handle null upside values
        const isNullUpsideA = upsideA === null || upsideA === undefined;
        const isNullUpsideB = upsideB === null || upsideB === undefined;
        
        if (isNullUpsideA && !isNullUpsideB) return 1;
        if (!isNullUpsideA && isNullUpsideB) return -1;
        if (isNullUpsideA && isNullUpsideB) return 0;
        
        return sortDirection === "desc" ? upsideB - upsideA : upsideA - upsideB;
      }
      
      // Special handling for Daily ST (Supertrend) column
      if (sortColumn === "daily_supertrend") {
        const directionA = a.daily_supertrend?.direction || "-";
        const directionB = b.daily_supertrend?.direction || "-";
        
        // Always put "-" values at the bottom
        if (directionA === "-" && directionB !== "-") return 1;
        if (directionA !== "-" && directionB === "-") return -1;
        if (directionA === "-" && directionB === "-") return 0;
        
        // Primary sorting: alphabetical on direction (UP/DOWN)
        if (directionA !== directionB) {
          if (sortDirection === "desc") {
            // desc: UP first, then DOWN
            return directionA === "UP" ? -1 : 1;
          } else {
            // asc: DOWN first, then UP
            return directionA === "DOWN" ? -1 : 1;
          }
        }
        
        // Secondary sorting: score
        const scoreA = a.scores?.total ?? -999;
        const scoreB = b.scores?.total ?? -999;
        if (scoreA !== scoreB) {
          return sortDirection === "desc" ? scoreB - scoreA : scoreA - scoreB;
        }
        
        // Tertiary sorting: % upside
        const upsideA = a.upside ?? -999;
        const upsideB = b.upside ?? -999;
        return sortDirection === "desc" ? upsideB - upsideA : upsideA - upsideB;
      }
      
      // Regular handling for other columns
      const valueA = getSortValue(a, sortColumn);
      const valueB = getSortValue(b, sortColumn);
      
      const isNullA = isNullValue(valueA);
      const isNullB = isNullValue(valueB);
      
      // Always put null values at the bottom
      if (isNullA && !isNullB) return 1;
      if (!isNullA && isNullB) return -1;
      if (isNullA && isNullB) return 0;
      
      // Alphabetical columns: Symbol, Sector, Industry, Init Trend
      if (["symbol", "sector", "industry", "init_trend"].includes(sortColumn)) {
        const strA = String(valueA).toLowerCase();
        const strB = String(valueB).toLowerCase();
        const comparison = strA.localeCompare(strB);
        return sortDirection === "desc" ? -comparison : comparison;
      }
      
      // Numeric/Percentage columns: all others
      const numA = parseFloat(valueA);
      const numB = parseFloat(valueB);
      
      if (isNaN(numA) && !isNaN(numB)) return 1;
      if (!isNaN(numA) && isNaN(numB)) return -1;
      if (isNaN(numA) && isNaN(numB)) return 0;
      
      return sortDirection === "desc" ? numB - numA : numA - numB;
    }
    
    // Default sorting (when no column is selected)
    const scoreA = a.scores?.total ?? -999;
    const scoreB = b.scores?.total ?? -999;
    const upsideA = a.upside ?? -999;
    const upsideB = b.upside ?? -999;

    if (filter === "all_down") {
      // For ALL UDTS DOWN: Primary sort ASCENDING by trend score, Secondary sort ASCENDING by upside %
      if (scoreA !== scoreB) {
        return scoreA - scoreB; // Ascending
      }
      return upsideA - upsideB; // Ascending (most negative first)
    } else {
      // For ALL UDTS UP and All Stocks: Primary sort DESCENDING by trend score, Secondary sort DESCENDING by upside %
      if (scoreA !== scoreB) {
        return scoreB - scoreA; // Descending
      }
      return upsideB - upsideA; // Descending
    }
  });

  // Count stats
  const totalStocks = stocks.length;
  const tripleUpCount = stocks.filter(s => s.is_triple_up).length;
  const tripleDownCount = stocks.filter(s => s.is_triple_down).length;
  const nifty50Count = stocks.filter(s => NIFTY50_SYMBOLS.includes(s.symbol)).length;
  const nonNifty50Count = stocks.filter(s => !NIFTY50_SYMBOLS.includes(s.symbol)).length;
  
  // Count ALL UP stocks (all 7 parameters UP + CMP="YES")
  const allUpCount = stocks.filter(s => {
    const allUp = s.udts?.monthly === "UP" && 
                  s.udts?.weekly === "UP" && 
                  s.udts?.daily === "UP" && 
                  s.udts?.["1hour"] === "UP" && 
                  s.udts?.["15min"] === "UP" &&
                  s.biggest_trend?.direction === "UP" &&
                  s.initial_trend?.direction === "UP" &&
                  s.cmp_label === "YES";
    return allUp;
  }).length;
  
  // Count ALL DOWN stocks (all 7 parameters DOWN + CMP="YES")
  const allDownCount = stocks.filter(s => {
    const allDown = s.udts?.monthly === "DOWN" && 
                    s.udts?.weekly === "DOWN" && 
                    s.udts?.daily === "DOWN" && 
                    s.udts?.["1hour"] === "DOWN" && 
                    s.udts?.["15min"] === "DOWN" &&
                    s.biggest_trend?.direction === "DOWN" &&
                    s.initial_trend?.direction === "DOWN" &&
                    s.cmp_label === "YES";
    return allDown;
  }).length;
  
  // Count UDTS UP/DOWN stocks (Triple UP + Triple DOWN)
  const udtsUpDownCount = tripleUpCount + tripleDownCount;

  // UDTS cell with support price and % distance in small font (for ALL stocks)
  const UdtsCell = ({ stock, timeframe }) => {
    const direction = stock.udts?.[timeframe];
    const support = stock.supports?.[timeframe];
    const distancePct = stock.support_distances?.[timeframe];
    
    return (
      <td className={direction === "UP" ? "cell-up" : direction === "DOWN" ? "cell-down" : ""}>
        {direction || "-"}
        {support && (
          <>
            <div className="small-text">{support.toFixed(2)}</div>
            {distancePct !== null && distancePct !== undefined && (
              <div className="small-text">{distancePct > 0 ? '+' : ''}{distancePct.toFixed(2)}%</div>
            )}
          </>
        )}
      </td>
    );
  };

  // Daily cell with support and % distance (for ALL stocks)
  const DailyCell = ({ stock }) => {
    const direction = stock.udts?.daily;
    const support = stock.supports?.daily;
    const distancePct = stock.support_distances?.daily;
    
    return (
      <td className={direction === "UP" ? "cell-up" : direction === "DOWN" ? "cell-down" : ""}>
        {direction || "-"}
        {support && (
          <>
            <div className="small-text">{support.toFixed(2)}</div>
            {distancePct !== null && distancePct !== undefined && (
              <div className="small-text">{distancePct > 0 ? '+' : ''}{distancePct.toFixed(2)}%</div>
            )}
          </>
        )}
      </td>
    );
  };

  // CMP cell with YES/NO label, CMP value, and change percentage
  const CmpCell = ({ stock }) => {
    const label = stock.cmp_label || "NO";
    const cmp = stock.cmp;
    const direction = stock.cmp_direction;
    const cmpChangePct = stock.cmp_change_pct;
    
    let cellClass = "cell-neutral";
    if (stock.is_triple_up) {
      cellClass = direction === "UP" ? "cell-up" : "cell-down";
    } else if (stock.is_triple_down) {
      cellClass = direction === "DOWN" ? "cell-down" : "cell-up";
    }
    
    return (
      <td className={cellClass}>
        {label}
        {cmp && <div className="small-text">{cmp.toFixed(2)}</div>}
        {cmpChangePct !== null && cmpChangePct !== undefined && (
          <div className="small-text">
            {cmpChangePct > 0 ? '+' : ''}{cmpChangePct.toFixed(2)}%
          </div>
        )}
      </td>
    );
  };

  // Biggest Trend cell
  const BigTrendCell = ({ stock }) => {
    const bt = stock.biggest_trend;
    if (!bt || !bt.direction) return <td>-</td>;
    
    const showDetails = isTriple(stock);
    
    // Calculate signed % distance from CMP to support
    let distanceFromCmp = null;
    if (bt.support && stock.cmp && stock.cmp > 0) {
      distanceFromCmp = ((bt.support - stock.cmp) / stock.cmp * 100).toFixed(2);
    }
    
    // Format candle info if available
    const formatCandle = (candle) => {
      if (!candle) return null;
      const date = candle.datetime ? new Date(candle.datetime).toLocaleDateString('en-IN', { 
        day: '2-digit', 
        month: 'short' 
      }) : '';
      return `${date}: ${candle.open?.toFixed(2)}-${candle.close?.toFixed(2)}`;
    };
    
    return (
      <td className={bt.direction === "UP" ? "cell-up" : "cell-down"}>
        {bt.direction}
        {showDetails && (
          <>
            <div className="small-text">
              {bt.support?.toFixed(2)} ({distanceFromCmp !== null ? (distanceFromCmp > 0 ? '+' : '') + distanceFromCmp : bt.distance_pct}%)
            </div>
            <div className="small-text">
              {bt.cmp_diff?.toFixed(2)}, {bt.low?.toFixed(2)}-{bt.high?.toFixed(2)}
            </div>
            {bt.start_candle && (
              <div className="small-text" style={{fontSize: '0.7em', color: '#666'}}>
                Start: {formatCandle(bt.start_candle)}
              </div>
            )}
            {bt.end_candle && (
              <div className="small-text" style={{fontSize: '0.7em', color: '#666'}}>
                End: {formatCandle(bt.end_candle)}
              </div>
            )}
          </>
        )}
      </td>
    );
  };

  // Initial Trend cell
  const InitTrendCell = ({ stock }) => {
    const it = stock.initial_trend;
    
    // Show blank only if no data exists
    if (!it || !it.direction) return <td>-</td>;
    
    return (
      <td className={it.direction === "UP" ? "cell-up" : "cell-down"}>
        {it.direction}
        {it.support && (
          <div className="small-text">{it.support.toFixed(2)}</div>
        )}
      </td>
    );
  };

  // Fundamental cell with color thresholds
  const FundCell = ({ value, thresholds, lowerBetter, decimals = 0 }) => {
    if (value === null || value === undefined) return <td className="cell-neutral">-</td>;
    
    let cellClass = "cell-neutral";
    const [green, yellow] = thresholds;
    
    if (lowerBetter) {
      if (value <= green) cellClass = "cell-up";
      else if (value <= yellow) cellClass = "cell-yellow";
      else cellClass = "cell-down";
    } else {
      if (value >= green) cellClass = "cell-up";
      else if (value >= yellow) cellClass = "cell-yellow";
      else cellClass = "cell-down";
    }
    
    return <td className={cellClass}>{value.toFixed(decimals)}</td>;
  };

  return (
    <div className="container" data-testid="app-container">
      {/* Sticky Header Wrapper */}
      <div className="sticky-header-wrapper">
        {/* Collapsible Header Section */}
        <Collapsible.Root open={isHeaderOpen} onOpenChange={setIsHeaderOpen}>
          <div style={{ 
            position: 'relative',
            minHeight: isHeaderOpen ? 'auto' : '48px'
          }}>
            <Collapsible.Content>
              {/* Header */}
              <div className="header" data-testid="header">
              {/* Row 1: Title, Pivot & Biggest Trend, NIFTY50 Live Level & A/D */}
              <div className="header-row-1">
                <h1>UDTS Stock Screener</h1>
                
                {/* Pivot and Biggest Trend - Center */}
                {nifty50 && nifty50.value && (
                  <div className="pivot-trend-line" data-testid="pivot-trend-line">
                    <span>
                      Pivot: <span className={nifty50.above_pivot ? "text-up" : "text-down"}>
                        {nifty50.above_pivot ? "UP" : "DOWN"} ({nifty50.pivot || "-"})
                      </span>
                    </span>
                    <span> AND </span>
                    <span>
                      Biggest Trend: <span className={nifty50.biggest_trend === "UP" ? "text-up" : "text-down"}>
                        {nifty50.biggest_trend || "-"} ({nifty50.biggest_trend_support || "-"})
                      </span>
                    </span>
                  </div>
                )}
                
                {/* NIFTY Info - Top Right */}
                {nifty50 && nifty50.value && (
                  <div className="nifty-info" data-testid="nifty-info">
                    <span className={nifty50.change_pct >= 0 ? "text-up" : "text-down"}>
                      NIFTY 50: {nifty50.value} ({nifty50.change_pct > 0 ? "+" : ""}{nifty50.change_pct}%)
                    </span>
                    <span>A/D: {nifty50.advance || 0}/{nifty50.decline || 0}</span>
                  </div>
                )}
              </div>
              
              {/* Row 2: Last Updated, Refresh Buttons, Stock Counts Summary */}
              <div className="header-row-2">
                {/* Last Updated On - Left */}
                <div className="last-updated" data-testid="last-updated">
                  Last Updated On: {lastUpdated ? new Date(lastUpdated).toLocaleString("en-IN") : "-"}
                </div>
                
                {/* Refresh Buttons - Center */}
                <div className="controls" data-testid="controls">
                  <button onClick={handleRefresh} disabled={loading} data-testid="refresh-btn">
                    {loading ? "Loading..." : "Refresh"}
                  </button>
                  <button 
                    onClick={handleRefreshStockList} 
                    disabled={refreshingList || loading} 
                    data-testid="refresh-stock-list-btn"
                    style={{ marginLeft: '10px' }}
                  >
                    {refreshingList ? "Refreshing List..." : "Refresh Stock List"}
                  </button>
                </div>
                
                {/* Stock Counts Summary - Right */}
                {!loading && stocks.length > 0 && (
                  <div className="stock-counts-summary" data-testid="stock-counts-summary">
                    <span>Number of UDTS UP/DOWN Stocks: <strong>{udtsUpDownCount}</strong></span>
                    <span> | </span>
                    <span>Total ALL UP Stocks: <strong className="text-up">{allUpCount}</strong></span>
                    <span> | </span>
                    <span>Total ALL DOWN Stocks: <strong className="text-down">{allDownCount}</strong></span>
                  </div>
                )}
              </div>
              
              {/* Refresh Message */}
              {listRefreshMessage && (
                <div className="refresh-message" style={{ textAlign: 'center', marginTop: '5px', fontSize: '0.9em' }}>
                  {listRefreshMessage}
                </div>
              )}
              
              {/* Row 3: Detailed Stock counts - Centered */}
              {!loading && stocks.length > 0 && (
                <div className="stock-counts" data-testid="stock-counts">
                  <span>Total: <strong>{totalStocks}</strong></span>
                  <span>NIFTY50: <strong>{nifty50Count}</strong></span>
                  <span>Non-NIFTY50: <strong>{nonNifty50Count}</strong></span>
                  <span>Filtered Stocks: <strong>{filteredStocks.length}</strong></span>
                  <span className="text-up">Triple UP: <strong>{tripleUpCount}</strong></span>
                  <span className="text-down">Triple DOWN: <strong>{tripleDownCount}</strong></span>
                </div>
              )}
              </div>
            </Collapsible.Content>
            
            {/* Header Toggle Button - Bottom Right Corner */}
            <Collapsible.Trigger asChild>
              <button 
                className="collapse-chevron-btn"
                data-testid="toggle-header-btn"
                title={isHeaderOpen ? 'Hide Header' : 'Show Header'}
                style={{
                  position: 'absolute',
                  bottom: '8px',
                  right: '8px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 10
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'scale(1.1)';
                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
                }}
              >
                {isHeaderOpen ? '▲' : '▼'}
              </button>
            </Collapsible.Trigger>
          </div>
        </Collapsible.Root>

        {/* Collapsible Filters Section */}
        <Collapsible.Root open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
          <div style={{ 
            position: 'relative',
            minHeight: isFiltersOpen ? 'auto' : '48px'
          }}>
            <Collapsible.Content>
              {/* All Filters in One Row */}
              <div className="filters-row-container" data-testid="filters-row-container">
            {/* UDTS Filter Slicer */}
            <div className="filter-slicer" data-testid="udts-filter-slicer">
              <span className="filter-label">UDTS:</span>
              <button 
                className={filter === "all" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setFilter("all")}
                data-testid="filter-all-stocks"
              >
                All
              </button>
              <button 
                className={filter === "all_up" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setFilter("all_up")}
                data-testid="filter-all-up"
              >
                All UP
              </button>
              <button 
                className={filter === "all_down" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setFilter("all_down")}
                data-testid="filter-all-down"
              >
                All DOWN
              </button>
            </div>

            {/* NIFTY Filter Slicer */}
            <div className="filter-slicer" data-testid="nifty-filter-slicer">
              <span className="filter-label">Type:</span>
              <button 
                className={niftyFilter === "all" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setNiftyFilter("all")}
                data-testid="nifty-filter-all"
              >
                All
              </button>
              <button 
                className={niftyFilter === "nifty50" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setNiftyFilter("nifty50")}
                data-testid="nifty-filter-nifty50"
              >
                N50
              </button>
              <button 
                className={niftyFilter === "non_nifty50" ? "slicer-btn active" : "slicer-btn"}
                onClick={() => setNiftyFilter("non_nifty50")}
                data-testid="nifty-filter-non-nifty50"
              >
                Non-N50
              </button>
            </div>
            
            {/* Column Filters Toggle */}
            <div className="filter-slicer" data-testid="column-filters-toggle">
              <button 
                className="slicer-btn"
                onClick={() => setShowFilters(!showFilters)}
                data-testid="toggle-column-filters"
              >
                {showFilters ? "Hide" : "Show"} columns
              </button>
              {showFilters && (
                <button 
                  className="slicer-btn"
                  onClick={() => setColumnFilters({
                    sector: "", industry: "",
                    monthly_trend: "all", weekly_trend: "all", daily_trend: "all",
                    cmp_change_min: "", cmp_change_max: "",
                    dist_min: "", dist_max: "", score_min: "", score_max: "",
                    upside_min: "", upside_max: "", two_yr_high_min: "", two_yr_high_max: "",
                    inst_hold_min: "", inst_hold_max: "",
                    mcap_min: "", mcap_max: "", roe_min: "", roe_max: "",
                    pe_min: "", pe_max: "", pb_min: "", pb_max: "",
                    de_min: "", de_max: "", rev_min: "", rev_max: "",
                    earn_min: "", earn_max: "", div_yield_min: "", div_yield_max: "",
                    net_income_min: "", net_income_max: "", ent_ebitda_min: "", ent_ebitda_max: "",
                    ent_rev_min: "", ent_rev_max: "",
                    daily_rsi_min: "", daily_rsi_max: "",
                    daily_adx_min: "", daily_adx_max: "",
                    daily_supertrend: "all",
                    daily_bb_pct_min: "", daily_bb_pct_max: "",
                    weekly_bb_pct_min: "", weekly_bb_pct_max: "",
                    monthly_bb_pct_min: "", monthly_bb_pct_max: ""
                  })}
                  data-testid="clear-all-filters"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Sectoral Analysis Button */}
            <div className="filter-slicer" data-testid="sectoral-analysis-toggle">
              <button 
                className="slicer-btn sectoral-btn"
                onClick={handleOpenSectorAnalysis}
                data-testid="sectoral-analysis-btn"
              >
                Sectors
              </button>
            </div>

            {/* Industry Analysis Button */}
            <div className="filter-slicer" data-testid="industry-analysis-toggle">
              <button 
                className="slicer-btn industry-btn"
                onClick={handleOpenIndustryAnalysis}
                data-testid="industry-analysis-btn"
              >
                Industries
              </button>
            </div>


            {/* BEST UU Preset Filter Button */}
            <div className="filter-slicer" data-testid="best-uu-filter-toggle">
              <button 
                className="slicer-btn preset-filter-btn"
                onClick={handleBestUUFilter}
                data-testid="best-uu-filter-btn"
                title="Filter: M=UP, W=UP, 2yr high%≥15, MCap≥20, ROE≥15, PE≤50, D/E≤50, Rev%≥0, Earn%≥0, Net Inc≥50"
              >
                Best UU
              </button>
            </div>

            {/* BEST Turn Preset Filter Button */}
            <div className="filter-slicer" data-testid="best-turn-filter-toggle">
              <button 
                className="slicer-btn preset-filter-btn"
                onClick={handleBestTurnFilter}
                data-testid="best-turn-filter-btn"
                title="Filter: M=DOWN, W=UP, D=UP, 2yr high%≥15, MCap≥20, ROE≥15, PE≤50, D/E≤50, Rev%≥0, Earn%≥0, Net Inc≥50"
              >
                Best turn
              </button>
            </div>

            {/* Clear Filters/Sort Button */}
            <div className="filter-slicer" data-testid="clear-filters-sort-toggle">
              <button 
                className="slicer-btn clear-btn"
                onClick={() => {
                  // Clear all filters
                  setColumnFilters({
                    sector: "", industry: "",
                    monthly_trend: "all", weekly_trend: "all", daily_trend: "all",
                    cmp_change_min: "", cmp_change_max: "",
                    dist_min: "", dist_max: "", score_min: "", score_max: "",
                    upside_min: "", upside_max: "", two_yr_high_min: "", two_yr_high_max: "",
                    inst_hold_min: "", inst_hold_max: "",
                    mcap_min: "", mcap_max: "", roe_min: "", roe_max: "",
                    pe_min: "", pe_max: "", pb_min: "", pb_max: "",
                    de_min: "", de_max: "", rev_min: "", rev_max: "",
                    earn_min: "", earn_max: "", div_yield_min: "", div_yield_max: "",
                    net_income_min: "", net_income_max: "", ent_ebitda_min: "", ent_ebitda_max: "",
                    ent_rev_min: "", ent_rev_max: "",
                    daily_rsi_min: "", daily_rsi_max: "",
                    daily_adx_min: "", daily_adx_max: "",
                    daily_supertrend: "all",
                    daily_bb_pct_min: "", daily_bb_pct_max: "",
                    weekly_bb_pct_min: "", weekly_bb_pct_max: "",
                    monthly_bb_pct_min: "", monthly_bb_pct_max: ""
                  });
                  // Clear sorting (back to default)
                  setSortColumn(null);
                  setSortDirection("desc");
                }}
                data-testid="clear-filters-sort-btn"
              >
                Clear all
              </button>
            </div>
          </div>
        </Collapsible.Content>
        
        {/* Filters Toggle Button - Bottom Right Corner */}
        <Collapsible.Trigger asChild>
          <button 
            className="collapse-chevron-btn"
            data-testid="toggle-filters-btn"
            title={isFiltersOpen ? 'Hide Filters' : 'Show Filters'}
            style={{
              position: 'absolute',
              bottom: '8px',
              right: '8px',
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              border: 'none',
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold',
              boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'scale(1.1)';
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
            }}
          >
            {isFiltersOpen ? '▲' : '▼'}
          </button>
        </Collapsible.Trigger>
          </div>
        </Collapsible.Root>
      </div>
      {/* End of Sticky Header Wrapper */}

      {/* Sector Analysis Modal */}
      {showSectorModal && (
        <div className="modal-overlay" onClick={() => setShowSectorModal(false)} data-testid="sector-modal-overlay">
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="sector-modal-content">
            <div className="modal-header">
              <h2>Sectoral Analysis</h2>
              <button className="modal-close" onClick={() => setShowSectorModal(false)}>×</button>
            </div>
            
            {loadingSectors ? (
              <div className="modal-loading">Loading sector analysis...</div>
            ) : (
              <div className="modal-body">
                {/* SUMMARY Section */}
                <div className="summary-section">
                  <h3>SUMMARY</h3>
                  <div className="summary-tables">
                    {/* Top 5 UP Trend Sectors */}
                    <div className="summary-table-container">
                      <h4 className="summary-title up">Top 5 UP Trend Sectors</h4>
                      <table className="summary-table">
                        <thead>
                          <tr>
                            <th>Sector</th>
                            <th>UDTS Score</th>
                            <th>Stock Count</th>
                            <th># Triple UP</th>
                            <th>% Triple UP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sectorTrends.up_trends.length > 0 ? (
                            sectorTrends.up_trends.map((trend, idx) => (
                              <tr key={idx}>
                                <td>{trend.sector}</td>
                                <td className="score-up">{trend.median_score}</td>
                                <td>{trend.stock_count}</td>
                                <td>{trend.fully_up_count}</td>
                                <td>{trend.pct_fully_up}%</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan="5">No UP trend sectors</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Top 5 DOWN Trend Sectors */}
                    <div className="summary-table-container">
                      <h4 className="summary-title down">Top 5 DOWN Trend Sectors</h4>
                      <table className="summary-table">
                        <thead>
                          <tr>
                            <th>Sector</th>
                            <th>UDTS Score</th>
                            <th>Stock Count</th>
                            <th># Triple DOWN</th>
                            <th>% Triple DOWN</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sectorTrends.down_trends.length > 0 ? (
                            sectorTrends.down_trends.map((trend, idx) => (
                              <tr key={idx}>
                                <td>{trend.sector}</td>
                                <td className="score-down">{trend.median_score}</td>
                                <td>{trend.stock_count}</td>
                                <td>{trend.fully_down_count}</td>
                                <td>{trend.pct_fully_down}%</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan="5">No DOWN trend sectors</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* DETAILS Section */}
                <div className="details-section">
                  <h3>DETAILS</h3>
                  
                  {/* Details for UP Trend Sectors */}
                  {sectorTrends.up_trends.map((trend, idx) => {
                    const sectorStocks = getStocksForSector(trend.sector);
                    return (
                      <div key={`up-${idx}`} className="detail-table-container">
                        <h4 className="detail-title up">{trend.sector} (UP Trend)</h4>
                        <table className="detail-table">
                          <thead>
                            <tr>
                              <th>Stock</th>
                              <th>Triple UDTS Score</th>
                              <th>Monthly</th>
                              <th>Weekly</th>
                              <th>Daily</th>
                              <th>Upside %</th>
                              <th>Dividend Yield</th>
                              <th>EV to EBITDA</th>
                              <th>EV to Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sectorStocks.length > 0 ? (
                              sectorStocks.map((stock) => (
                                <tr key={stock.symbol}>
                                  <td className="stock-name">{stock.symbol}</td>
                                  <td className={stock.tripleScore > 0 ? "score-up" : stock.tripleScore < 0 ? "score-down" : ""}>
                                    {stock.tripleScore}
                                  </td>
                                  <td className={stock.monthlyTrend === "UP" ? "trend-up" : stock.monthlyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.monthlyTrend}
                                  </td>
                                  <td className={stock.weeklyTrend === "UP" ? "trend-up" : stock.weeklyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.weeklyTrend}
                                  </td>
                                  <td className={stock.dailyTrend === "UP" ? "trend-up" : stock.dailyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.dailyTrend}
                                  </td>
                                  <td className={stock.upsidePct > 10 ? "score-up" : stock.upsidePct < 0 ? "score-down" : ""}>
                                    {stock.upsidePct !== null && stock.upsidePct !== undefined ? stock.upsidePct.toFixed(1) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.dividendYield !== null && stock.dividendYield !== undefined ? stock.dividendYield.toFixed(2) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.evToEbitda !== null && stock.evToEbitda !== undefined ? stock.evToEbitda.toFixed(2) : "-"}
                                  </td>
                                  <td>
                                    {stock.evToRevenue !== null && stock.evToRevenue !== undefined ? stock.evToRevenue.toFixed(2) : "-"}
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr><td colSpan="9">No stocks in this sector</td></tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    );
                  })}

                  {/* Details for DOWN Trend Sectors */}
                  {sectorTrends.down_trends.map((trend, idx) => {
                    const sectorStocks = getStocksForSector(trend.sector, true);
                    return (
                      <div key={`down-${idx}`} className="detail-table-container">
                        <h4 className="detail-title down">{trend.sector} (DOWN Trend)</h4>
                        <table className="detail-table">
                          <thead>
                            <tr>
                              <th>Stock</th>
                              <th>Triple UDTS Score</th>
                              <th>Monthly</th>
                              <th>Weekly</th>
                              <th>Daily</th>
                              <th>Upside %</th>
                              <th>Dividend Yield</th>
                              <th>EV to EBITDA</th>
                              <th>EV to Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sectorStocks.length > 0 ? (
                              sectorStocks.map((stock) => (
                                <tr key={stock.symbol}>
                                  <td className="stock-name">{stock.symbol}</td>
                                  <td className={stock.tripleScore > 0 ? "score-up" : stock.tripleScore < 0 ? "score-down" : ""}>
                                    {stock.tripleScore}
                                  </td>
                                  <td className={stock.monthlyTrend === "UP" ? "trend-up" : stock.monthlyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.monthlyTrend}
                                  </td>
                                  <td className={stock.weeklyTrend === "UP" ? "trend-up" : stock.weeklyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.weeklyTrend}
                                  </td>
                                  <td className={stock.dailyTrend === "UP" ? "trend-up" : stock.dailyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.dailyTrend}
                                  </td>
                                  <td className={stock.upsidePct > 10 ? "score-up" : stock.upsidePct < 0 ? "score-down" : ""}>
                                    {stock.upsidePct !== null && stock.upsidePct !== undefined ? stock.upsidePct.toFixed(1) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.dividendYield !== null && stock.dividendYield !== undefined ? stock.dividendYield.toFixed(2) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.evToEbitda !== null && stock.evToEbitda !== undefined ? stock.evToEbitda.toFixed(2) : "-"}
                                  </td>
                                  <td>
                                    {stock.evToRevenue !== null && stock.evToRevenue !== undefined ? stock.evToRevenue.toFixed(2) : "-"}
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr><td colSpan="9">No stocks in this sector</td></tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Industry Analysis Modal */}
      {showIndustryModal && (
        <div className="modal-overlay" onClick={() => setShowIndustryModal(false)} data-testid="industry-modal-overlay">
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="industry-modal-content">
            <div className="modal-header">
              <h2>Industry Analysis</h2>
              <button className="modal-close" onClick={() => setShowIndustryModal(false)}>×</button>
            </div>
            
            {loadingIndustries ? (
              <div className="modal-loading">Loading industry analysis...</div>
            ) : (
              <div className="modal-body">
                {/* SUMMARY Section */}
                <div className="summary-section">
                  <h3>SUMMARY</h3>
                  <div className="summary-tables">
                    {/* Top 10 UP Trend Industries */}
                    <div className="summary-table-container">
                      <h4 className="summary-title up">Top 10 UP Trend Industries</h4>
                      <table className="summary-table">
                        <thead>
                          <tr>
                            <th>Industry</th>
                            <th>UDTS Score</th>
                            <th>Stock Count</th>
                            <th># Triple UP</th>
                            <th>% Triple UP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {industryTrends.up_trends.length > 0 ? (
                            industryTrends.up_trends.map((trend, idx) => (
                              <tr key={idx}>
                                <td>{trend.industry}</td>
                                <td className="score-up">{trend.median_score}</td>
                                <td>{trend.stock_count}</td>
                                <td>{trend.fully_up_count}</td>
                                <td>{trend.pct_fully_up}%</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan="5">No UP trend industries</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Top 10 DOWN Trend Industries */}
                    <div className="summary-table-container">
                      <h4 className="summary-title down">Top 10 DOWN Trend Industries</h4>
                      <table className="summary-table">
                        <thead>
                          <tr>
                            <th>Industry</th>
                            <th>UDTS Score</th>
                            <th>Stock Count</th>
                            <th># Triple DOWN</th>
                            <th>% Triple DOWN</th>
                          </tr>
                        </thead>
                        <tbody>
                          {industryTrends.down_trends.length > 0 ? (
                            industryTrends.down_trends.map((trend, idx) => (
                              <tr key={idx}>
                                <td>{trend.industry}</td>
                                <td className="score-down">{trend.median_score}</td>
                                <td>{trend.stock_count}</td>
                                <td>{trend.fully_down_count}</td>
                                <td>{trend.pct_fully_down}%</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan="5">No DOWN trend industries</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* DETAILS Section */}
                <div className="details-section">
                  <h3>DETAILS</h3>
                  
                  {/* Details for UP Trend Industries */}
                  {industryTrends.up_trends.map((trend, idx) => {
                    const industryStocks = getStocksForIndustry(trend.industry);
                    return (
                      <div key={`up-${idx}`} className="detail-table-container">
                        <h4 className="detail-title up">{trend.industry} (UP Trend)</h4>
                        <table className="detail-table">
                          <thead>
                            <tr>
                              <th>Stock</th>
                              <th>Triple UDTS Score</th>
                              <th>Monthly</th>
                              <th>Weekly</th>
                              <th>Daily</th>
                              <th>Upside %</th>
                              <th>Dividend Yield</th>
                              <th>EV to EBITDA</th>
                              <th>EV to Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {industryStocks.length > 0 ? (
                              industryStocks.map((stock) => (
                                <tr key={stock.symbol}>
                                  <td className="stock-name">{stock.symbol}</td>
                                  <td className={stock.tripleScore > 0 ? "score-up" : stock.tripleScore < 0 ? "score-down" : ""}>
                                    {stock.tripleScore}
                                  </td>
                                  <td className={stock.monthlyTrend === "UP" ? "trend-up" : stock.monthlyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.monthlyTrend}
                                  </td>
                                  <td className={stock.weeklyTrend === "UP" ? "trend-up" : stock.weeklyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.weeklyTrend}
                                  </td>
                                  <td className={stock.dailyTrend === "UP" ? "trend-up" : stock.dailyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.dailyTrend}
                                  </td>
                                  <td className={stock.upsidePct > 10 ? "score-up" : stock.upsidePct < 0 ? "score-down" : ""}>
                                    {stock.upsidePct !== null && stock.upsidePct !== undefined ? stock.upsidePct.toFixed(1) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.dividendYield !== null && stock.dividendYield !== undefined ? stock.dividendYield.toFixed(2) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.evToEbitda !== null && stock.evToEbitda !== undefined ? stock.evToEbitda.toFixed(2) : "-"}
                                  </td>
                                  <td>
                                    {stock.evToRevenue !== null && stock.evToRevenue !== undefined ? stock.evToRevenue.toFixed(2) : "-"}
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr><td colSpan="9">No stocks in this industry</td></tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    );
                  })}

                  {/* Details for DOWN Trend Industries */}
                  {industryTrends.down_trends.map((trend, idx) => {
                    const industryStocks = getStocksForIndustry(trend.industry, true);
                    return (
                      <div key={`down-${idx}`} className="detail-table-container">
                        <h4 className="detail-title down">{trend.industry} (DOWN Trend)</h4>
                        <table className="detail-table">
                          <thead>
                            <tr>
                              <th>Stock</th>
                              <th>Triple UDTS Score</th>
                              <th>Monthly</th>
                              <th>Weekly</th>
                              <th>Daily</th>
                              <th>Upside %</th>
                              <th>Dividend Yield</th>
                              <th>EV to EBITDA</th>
                              <th>EV to Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {industryStocks.length > 0 ? (
                              industryStocks.map((stock) => (
                                <tr key={stock.symbol}>
                                  <td className="stock-name">{stock.symbol}</td>
                                  <td className={stock.tripleScore > 0 ? "score-up" : stock.tripleScore < 0 ? "score-down" : ""}>
                                    {stock.tripleScore}
                                  </td>
                                  <td className={stock.monthlyTrend === "UP" ? "trend-up" : stock.monthlyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.monthlyTrend}
                                  </td>
                                  <td className={stock.weeklyTrend === "UP" ? "trend-up" : stock.weeklyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.weeklyTrend}
                                  </td>
                                  <td className={stock.dailyTrend === "UP" ? "trend-up" : stock.dailyTrend === "DOWN" ? "trend-down" : ""}>
                                    {stock.dailyTrend}
                                  </td>
                                  <td className={stock.upsidePct > 10 ? "score-up" : stock.upsidePct < 0 ? "score-down" : ""}>
                                    {stock.upsidePct !== null && stock.upsidePct !== undefined ? stock.upsidePct.toFixed(1) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.dividendYield !== null && stock.dividendYield !== undefined ? stock.dividendYield.toFixed(2) + "%" : "-"}
                                  </td>
                                  <td>
                                    {stock.evToEbitda !== null && stock.evToEbitda !== undefined ? stock.evToEbitda.toFixed(2) : "-"}
                                  </td>
                                  <td>
                                    {stock.evToRevenue !== null && stock.evToRevenue !== undefined ? stock.evToRevenue.toFixed(2) : "-"}
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr><td colSpan="9">No stocks in this industry</td></tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Column Filters Panel */}
      {showFilters && (
        <div className="column-filters-panel" data-testid="column-filters-panel">
          <div className="filters-grid">
            {/* Text Filters */}
            <div className="filter-group">
              <label>Sector:</label>
              <input 
                type="text" 
                value={columnFilters.sector}
                onChange={(e) => setColumnFilters({...columnFilters, sector: e.target.value})}
                placeholder="Search..."
                data-testid="filter-sector"
              />
            </div>
            
            <div className="filter-group">
              <label>Industry:</label>
              <input 
                type="text" 
                value={columnFilters.industry}
                onChange={(e) => setColumnFilters({...columnFilters, industry: e.target.value})}
                placeholder="Search..."
                data-testid="filter-industry"
              />
            </div>
            
            {/* Trend Direction Filters */}
            <div className="filter-group">
              <label>M (UP/DOWN):</label>
              <select 
                value={columnFilters.monthly_trend}
                onChange={(e) => setColumnFilters({...columnFilters, monthly_trend: e.target.value})}
                data-testid="filter-monthly-trend"
              >
                <option value="all">All</option>
                <option value="UP">UP</option>
                <option value="DOWN">DOWN</option>
              </select>
            </div>
            
            <div className="filter-group">
              <label>W (UP/DOWN):</label>
              <select 
                value={columnFilters.weekly_trend}
                onChange={(e) => setColumnFilters({...columnFilters, weekly_trend: e.target.value})}
                data-testid="filter-weekly-trend"
              >
                <option value="all">All</option>
                <option value="UP">UP</option>
                <option value="DOWN">DOWN</option>
              </select>
            </div>
            
            <div className="filter-group">
              <label>D (UP/DOWN):</label>
              <select 
                value={columnFilters.daily_trend}
                onChange={(e) => setColumnFilters({...columnFilters, daily_trend: e.target.value})}
                data-testid="filter-daily-trend"
              >
                <option value="all">All</option>
                <option value="UP">UP</option>
                <option value="DOWN">DOWN</option>
              </select>
            </div>
            
            {/* CMP % Change Filter */}
            <div className="filter-group filter-range">
              <label>CMP % change:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.01"
                  value={columnFilters.cmp_change_min}
                  onChange={(e) => setColumnFilters({...columnFilters, cmp_change_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-cmp-change-min"
                />
                <input 
                  type="number" 
                  step="0.01"
                  value={columnFilters.cmp_change_max}
                  onChange={(e) => setColumnFilters({...columnFilters, cmp_change_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-cmp-change-max"
                />
              </div>
            </div>
            
            {/* Dist% Filter */}
            <div className="filter-group filter-range">
              <label>Dist%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.dist_min}
                  onChange={(e) => setColumnFilters({...columnFilters, dist_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-dist-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.dist_max}
                  onChange={(e) => setColumnFilters({...columnFilters, dist_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-dist-max"
                />
              </div>
            </div>
            
            {/* Score Filter */}
            <div className="filter-group filter-range">
              <label>Score:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.score_min}
                  onChange={(e) => setColumnFilters({...columnFilters, score_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-score-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.score_max}
                  onChange={(e) => setColumnFilters({...columnFilters, score_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-score-max"
                />
              </div>
            </div>
            
            {/* Up% Filter */}
            <div className="filter-group filter-range">
              <label>Up%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.upside_min}
                  onChange={(e) => setColumnFilters({...columnFilters, upside_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-upside-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.upside_max}
                  onChange={(e) => setColumnFilters({...columnFilters, upside_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-upside-max"
                />
              </div>
            </div>
            
            {/* 2yr high % Filter */}
            <div className="filter-group filter-range">
              <label>2yr high %:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.two_yr_high_min}
                  onChange={(e) => setColumnFilters({...columnFilters, two_yr_high_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-two-yr-high-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.two_yr_high_max}
                  onChange={(e) => setColumnFilters({...columnFilters, two_yr_high_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-two-yr-high-max"
                />
              </div>
            </div>
            
            {/* Inst. Hold% Filter */}
            <div className="filter-group filter-range">
              <label>Inst. Hold%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.01"
                  value={columnFilters.inst_hold_min}
                  onChange={(e) => setColumnFilters({...columnFilters, inst_hold_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-inst-hold-min"
                />
                <input 
                  type="number" 
                  step="0.01"
                  value={columnFilters.inst_hold_max}
                  onChange={(e) => setColumnFilters({...columnFilters, inst_hold_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-inst-hold-max"
                />
              </div>
            </div>
            
            {/* MCap Filter */}
            <div className="filter-group filter-range">
              <label>MCap(TkCr):</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.mcap_min}
                  onChange={(e) => setColumnFilters({...columnFilters, mcap_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-mcap-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.mcap_max}
                  onChange={(e) => setColumnFilters({...columnFilters, mcap_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-mcap-max"
                />
              </div>
            </div>
            
            {/* ROE Filter */}
            <div className="filter-group filter-range">
              <label>ROE:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.roe_min}
                  onChange={(e) => setColumnFilters({...columnFilters, roe_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-roe-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.roe_max}
                  onChange={(e) => setColumnFilters({...columnFilters, roe_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-roe-max"
                />
              </div>
            </div>
            
            {/* PE Filter */}
            <div className="filter-group filter-range">
              <label>PE:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.pe_min}
                  onChange={(e) => setColumnFilters({...columnFilters, pe_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-pe-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.pe_max}
                  onChange={(e) => setColumnFilters({...columnFilters, pe_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-pe-max"
                />
              </div>
            </div>
            
            {/* PB Filter */}
            <div className="filter-group filter-range">
              <label>P/B:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.pb_min}
                  onChange={(e) => setColumnFilters({...columnFilters, pb_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-pb-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.pb_max}
                  onChange={(e) => setColumnFilters({...columnFilters, pb_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-pb-max"
                />
              </div>
            </div>
            
            {/* DE Filter */}
            <div className="filter-group filter-range">
              <label>D/E:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.de_min}
                  onChange={(e) => setColumnFilters({...columnFilters, de_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-de-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.de_max}
                  onChange={(e) => setColumnFilters({...columnFilters, de_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-de-max"
                />
              </div>
            </div>
            
            {/* Rev% Filter */}
            <div className="filter-group filter-range">
              <label>Rev%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.rev_min}
                  onChange={(e) => setColumnFilters({...columnFilters, rev_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-rev-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.rev_max}
                  onChange={(e) => setColumnFilters({...columnFilters, rev_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-rev-max"
                />
              </div>
            </div>
            
            {/* Earn% Filter */}
            <div className="filter-group filter-range">
              <label>Earn%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.earn_min}
                  onChange={(e) => setColumnFilters({...columnFilters, earn_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-earn-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.earn_max}
                  onChange={(e) => setColumnFilters({...columnFilters, earn_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-earn-max"
                />
              </div>
            </div>
            
            {/* Dividend Yield% Filter */}
            <div className="filter-group filter-range">
              <label>Div Yield%:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.div_yield_min}
                  onChange={(e) => setColumnFilters({...columnFilters, div_yield_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-div-yield-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.div_yield_max}
                  onChange={(e) => setColumnFilters({...columnFilters, div_yield_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-div-yield-max"
                />
              </div>
            </div>
            
            {/* Net Income Filter */}
            <div className="filter-group filter-range">
              <label>Net Inc(Cr):</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  value={columnFilters.net_income_min}
                  onChange={(e) => setColumnFilters({...columnFilters, net_income_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-net-income-min"
                />
                <input 
                  type="number" 
                  value={columnFilters.net_income_max}
                  onChange={(e) => setColumnFilters({...columnFilters, net_income_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-net-income-max"
                />
              </div>
            </div>
            
            {/* Enterprise to EBITDA Filter */}
            <div className="filter-group filter-range">
              <label>Ent/EBITDA:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.ent_ebitda_min}
                  onChange={(e) => setColumnFilters({...columnFilters, ent_ebitda_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-ent-ebitda-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.ent_ebitda_max}
                  onChange={(e) => setColumnFilters({...columnFilters, ent_ebitda_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-ent-ebitda-max"
                />
              </div>
            </div>
            
            {/* Enterprise to Revenue Filter */}
            <div className="filter-group filter-range">
              <label>Ent/Rev:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.ent_rev_min}
                  onChange={(e) => setColumnFilters({...columnFilters, ent_rev_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-ent-rev-min"
                />
                <input 
                  type="number" 
                  step="0.1"
                  value={columnFilters.ent_rev_max}
                  onChange={(e) => setColumnFilters({...columnFilters, ent_rev_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-ent-rev-max"
                />
              </div>
            </div>
            
            {/* NEW Technical Indicator Filters - 6 fields */}
            <div className="filter-group filter-range">
              <label>Daily RSI:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_rsi_min}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_rsi_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-daily-rsi-min"
                />
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_rsi_max}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_rsi_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-daily-rsi-max"
                />
              </div>
            </div>
            
            <div className="filter-group filter-range">
              <label>Daily ADX:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_adx_min}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_adx_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-daily-adx-min"
                />
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_adx_max}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_adx_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-daily-adx-max"
                />
              </div>
            </div>
            
            <div className="filter-group">
              <label>Daily ST (UP/DOWN):</label>
              <select 
                value={columnFilters.daily_supertrend}
                onChange={(e) => setColumnFilters({...columnFilters, daily_supertrend: e.target.value})}
                data-testid="filter-daily-supertrend"
              >
                <option value="all">All</option>
                <option value="UP">UP</option>
                <option value="DOWN">DOWN</option>
              </select>
            </div>
            
            <div className="filter-group filter-range">
              <label>Daily %BB:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_bb_pct_min}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_bb_pct_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-daily-bb-pct-min"
                />
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.daily_bb_pct_max}
                  onChange={(e) => setColumnFilters({...columnFilters, daily_bb_pct_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-daily-bb-pct-max"
                />
              </div>
            </div>
            
            <div className="filter-group filter-range">
              <label>Weekly %BB:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.weekly_bb_pct_min}
                  onChange={(e) => setColumnFilters({...columnFilters, weekly_bb_pct_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-weekly-bb-pct-min"
                />
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.weekly_bb_pct_max}
                  onChange={(e) => setColumnFilters({...columnFilters, weekly_bb_pct_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-weekly-bb-pct-max"
                />
              </div>
            </div>
            
            <div className="filter-group filter-range">
              <label>Monthly %BB:</label>
              <div className="range-inputs">
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.monthly_bb_pct_min}
                  onChange={(e) => setColumnFilters({...columnFilters, monthly_bb_pct_min: e.target.value})}
                  placeholder="Min"
                  data-testid="filter-monthly-bb-pct-min"
                />
                <input 
                  type="number" 
                  step="1"
                  value={columnFilters.monthly_bb_pct_max}
                  onChange={(e) => setColumnFilters({...columnFilters, monthly_bb_pct_max: e.target.value})}
                  placeholder="Max"
                  data-testid="filter-monthly-bb-pct-max"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="table-wrapper" data-testid="table-wrapper">
        <table data-testid="stocks-table">
          <thead>
            <tr>
              <th onClick={() => handleColumnSort("symbol")} style={{cursor: "pointer"}} data-testid="th-symbol">
                Stock {sortColumn === "symbol" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("sector")} style={{cursor: "pointer"}} data-testid="th-sector">
                Sector {sortColumn === "sector" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("industry")} style={{cursor: "pointer"}} data-testid="th-industry">
                Industry {sortColumn === "industry" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("monthly")} style={{cursor: "pointer"}} data-testid="th-monthly">
                M {sortColumn === "monthly" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("weekly")} style={{cursor: "pointer"}} data-testid="th-weekly">
                W {sortColumn === "weekly" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("daily")} style={{cursor: "pointer"}} data-testid="th-daily">
                D {sortColumn === "daily" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("hourly")} style={{cursor: "pointer"}} data-testid="th-hourly">
                1H {sortColumn === "hourly" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("min15")} style={{cursor: "pointer"}} data-testid="th-min15">
                15m {sortColumn === "min15" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("cmp")} style={{cursor: "pointer"}} data-testid="th-cmp">
                CMP {sortColumn === "cmp" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("big_trend")} style={{cursor: "pointer"}} data-testid="th-big-trend">
                Big Trend {sortColumn === "big_trend" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("init_trend")} style={{cursor: "pointer"}} data-testid="th-init-trend">
                Init Trend {sortColumn === "init_trend" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("dist")} style={{cursor: "pointer"}} data-testid="th-dist">
                Dist% {sortColumn === "dist" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("score")} style={{cursor: "pointer"}} data-testid="th-score">
                Score {sortColumn === "score" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("upside")} style={{cursor: "pointer"}} data-testid="th-upside">
                Up% {sortColumn === "upside" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("two_yr_high")} style={{cursor: "pointer"}} data-testid="th-two-yr-high">
                2yr high % {sortColumn === "two_yr_high" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("inst_hold")} style={{cursor: "pointer"}} data-testid="th-inst-hold">
                Inst. Hold% {sortColumn === "inst_hold" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("mcap")} style={{cursor: "pointer"}} data-testid="th-mcap">
                MCap(TkCr) {sortColumn === "mcap" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("roe")} style={{cursor: "pointer"}} data-testid="th-roe">
                ROE {sortColumn === "roe" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("pe")} style={{cursor: "pointer"}} data-testid="th-pe">
                PE {sortColumn === "pe" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("pb")} style={{cursor: "pointer"}} data-testid="th-pb">
                P/B {sortColumn === "pb" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("de")} style={{cursor: "pointer"}} data-testid="th-de">
                D/E {sortColumn === "de" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("rev")} style={{cursor: "pointer"}} data-testid="th-rev">
                Rev% {sortColumn === "rev" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("earn")} style={{cursor: "pointer"}} data-testid="th-earn">
                Earn% {sortColumn === "earn" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("div_yield")} style={{cursor: "pointer"}} data-testid="th-div-yield">
                Div Yield% {sortColumn === "div_yield" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("net_income")} style={{cursor: "pointer"}} data-testid="th-net-income">
                Net Inc(Cr) {sortColumn === "net_income" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("ent_ebitda")} style={{cursor: "pointer"}} data-testid="th-ent-ebitda">
                Ent/EBITDA {sortColumn === "ent_ebitda" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("ent_rev")} style={{cursor: "pointer"}} data-testid="th-ent-rev">
                Ent/Rev {sortColumn === "ent_rev" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("daily_rsi")} style={{cursor: "pointer"}} data-testid="th-daily-rsi">
                Daily RSI {sortColumn === "daily_rsi" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("daily_adx")} style={{cursor: "pointer"}} data-testid="th-daily-adx">
                Daily ADX {sortColumn === "daily_adx" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("daily_supertrend")} style={{cursor: "pointer"}} data-testid="th-daily-supertrend">
                Daily ST {sortColumn === "daily_supertrend" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("daily_bb_pct")} style={{cursor: "pointer"}} data-testid="th-daily-bb-pct">
                Daily %BB {sortColumn === "daily_bb_pct" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("weekly_bb_pct")} style={{cursor: "pointer"}} data-testid="th-weekly-bb-pct">
                Weekly %BB {sortColumn === "weekly_bb_pct" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
              <th onClick={() => handleColumnSort("monthly_bb_pct")} style={{cursor: "pointer"}} data-testid="th-monthly-bb-pct">
                Monthly %BB {sortColumn === "monthly_bb_pct" && (sortDirection === "desc" ? "▼" : "▲")}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedFilteredStocks.slice(0, displayLimit).map((s) => (
              <tr 
                key={s.symbol} 
                className={s.is_triple_up ? "row-triple-up" : s.is_triple_down ? "row-triple-down" : ""} 
                data-testid={`stock-row-${s.symbol}`}
              >
                <td className="cell-symbol">{s.symbol}</td>
                <td className="cell-sector">{s.sector || "-"}</td>
                <td className="cell-industry">{s.industry || "-"}</td>
                <UdtsCell stock={s} timeframe="monthly" />
                <UdtsCell stock={s} timeframe="weekly" />
                <DailyCell stock={s} />
                <UdtsCell stock={s} timeframe="1hour" />
                <UdtsCell stock={s} timeframe="15min" />
                <CmpCell stock={s} />
                <BigTrendCell stock={s} />
                <InitTrendCell stock={s} />
                <td>{s.max_distance !== null && s.max_distance !== undefined ? (s.max_distance > 0 ? '+' : '') + s.max_distance + "%" : "-"}</td>
                <td className={s.scores?.total > 0 ? "cell-up" : s.scores?.total < 0 ? "cell-down" : "cell-neutral"}>
                  {s.scores?.total ?? "-"}
                </td>
                <td className={s.upside > 10 ? "cell-up" : s.upside < 0 ? "cell-down" : "cell-neutral"}>
                  {s.upside !== null && s.upside !== undefined ? s.upside + "%" : "-"}
                  {s.target_price && <div className="small-text">{s.target_price.toFixed(2)}</div>}
                  {s.analyst_count && <div className="small-text">{s.analyst_count} analysts</div>}
                </td>
                <td className={s.two_yr_high_pct > 10 ? "cell-up" : s.two_yr_high_pct < 0 ? "cell-down" : "cell-neutral"}>
                  {s.two_yr_high_pct !== null && s.two_yr_high_pct !== undefined ? s.two_yr_high_pct.toFixed(2) + "%" : "-"}
                </td>
                <td className="cell-neutral">
                  {s.inst_holding_pct && s.inst_holding_pct !== "NA" 
                    ? parseFloat(s.inst_holding_pct).toFixed(2) + "%" 
                    : s.inst_holding_pct === "NA" ? "NA" : "-"}
                </td>
                <td className="cell-neutral">
                  {s.market_cap_tkc !== null && s.market_cap_tkc !== undefined ? Math.round(s.market_cap_tkc) : "-"}
                </td>
                <FundCell value={s.fundamentals?.roe} thresholds={[15, 10]} lowerBetter={false} />
                <FundCell value={s.fundamentals?.pe} thresholds={[20, 30]} lowerBetter={true} />
                <FundCell value={s.fundamentals?.pb} thresholds={[3, 6]} lowerBetter={true} />
                <FundCell value={s.fundamentals?.de} thresholds={[50, 100]} lowerBetter={true} />
                <FundCell value={s.fundamentals?.revenue_growth} thresholds={[10, 5]} lowerBetter={false} />
                <FundCell value={s.fundamentals?.earnings_growth} thresholds={[12, 6]} lowerBetter={false} />
                <FundCell value={s.fundamentals?.dividend_yield} thresholds={[2, 1]} lowerBetter={false} />
                <FundCell value={s.fundamentals?.net_income_to_common} thresholds={[100, 50]} lowerBetter={false} />
                <FundCell value={s.fundamentals?.enterprise_to_ebitda} thresholds={[10, 15]} lowerBetter={true} decimals={1} />
                <FundCell value={s.fundamentals?.enterprise_to_revenue} thresholds={[3, 5]} lowerBetter={true} decimals={1} />
                <td className="cell-neutral">
                  {s.daily_rsi !== null && s.daily_rsi !== undefined ? s.daily_rsi : "-"}
                </td>
                <td className="cell-neutral">
                  {s.daily_adx !== null && s.daily_adx !== undefined ? s.daily_adx : "-"}
                </td>
                <td className={s.daily_supertrend?.direction === "UP" ? "cell-up" : s.daily_supertrend?.direction === "DOWN" ? "cell-down" : "cell-neutral"}>
                  {s.daily_supertrend ? (
                    <>
                      <div>{s.daily_supertrend.direction}</div>
                      <div className="small-text">{s.daily_supertrend.level}</div>
                    </>
                  ) : "-"}
                </td>
                <td className="cell-neutral">
                  {s.daily_bb_pct !== null && s.daily_bb_pct !== undefined ? s.daily_bb_pct + "%" : "-"}
                </td>
                <td className="cell-neutral">
                  {s.weekly_bb_pct !== null && s.weekly_bb_pct !== undefined ? s.weekly_bb_pct + "%" : "-"}
                </td>
                <td className="cell-neutral">
                  {s.monthly_bb_pct !== null && s.monthly_bb_pct !== undefined ? s.monthly_bb_pct + "%" : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Show More button for large datasets */}
      {!loading && sortedFilteredStocks.length > displayLimit && (
        <div style={{textAlign: "center", padding: "20px"}}>
          <button 
            onClick={() => setDisplayLimit(prev => prev + 100)}
            style={{
              padding: "10px 30px",
              fontSize: "16px",
              backgroundColor: "#4CAF50",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer"
            }}
            data-testid="show-more-button"
          >
            Show More ({sortedFilteredStocks.length - displayLimit} remaining)
          </button>
        </div>
      )}
      
      {loading && (
        <div className="loading" data-testid="loading">
          <p><strong>⏳ Loading stock data from NSE for 500 stocks...</strong></p>
          <p>Loading time: <strong>{Math.floor(loadingTime / 60)} minutes {loadingTime % 60} seconds</strong></p>
          <p>This process can take <strong>30-90 minutes or longer</strong> as it fetches real-time data from multiple sources.</p>
          <p>Each stock requires data from 5 timeframes plus fundamental analysis.</p>
          <p><strong>Please be patient and do not refresh the page. Timeout set to 24 hours - no timeout errors!</strong></p>
          <p className="small-text">The application will load automatically once data is ready.</p>
        </div>
      )}
      {!loading && filteredStocks.length === 0 && stocks.length === 0 && <div className="no-data">No stocks loaded yet. Please wait for data to load or click Refresh.</div>}
      {!loading && filteredStocks.length === 0 && stocks.length > 0 && <div className="no-data">No stocks match the selected filters.</div>}
    </div>
  );
}

export default App;
