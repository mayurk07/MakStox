from fastapi import FastAPI, APIRouter, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd
import time
import threading
import requests
from bs4 import BeautifulSoup
import csv
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import ta  # Technical Analysis library
from database import (
    init_supabase,
    SUPABASE_AVAILABLE,
    get_ohlc_cache,
    save_ohlc_cache,
    get_fundamentals_cache,
    save_fundamentals_cache,
    get_institutional_cache,
    save_institutional_cache,
    get_stock_list,
    save_stock_list,
    clear_all_caches,
    get_ist_now as db_get_ist_now
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Supabase database
init_supabase()

# In-memory cache (fallback)
cache = {
    "ohlc": {},
    "fundamentals": {},
    "institutional_holdings": {},
    "nifty500_list": {"data": None, "timestamp": None},
    "nifty50_list": {"data": None, "timestamp": None},
    "nifty50": {"data": None, "timestamp": None}
}
cache_lock = threading.Lock()

# NIFTY 50 constituents - Updated January 2025 (fallback list)
NIFTY50_SYMBOLS = [
    "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BHARTIARTL", "BPCL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GAIL", "GRASIM",
    "HCLTECH", "HDFC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "INDUSINDBK", "INFY", "IOC", "ITC", "JSWSTEEL", "KOTAKBANK", "LT", "M&M",
    "MARUTI", "NESTLEIND", "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
    "SHREECEM", "SUNPHARMA", "TATAMOTORS", "TATASTEEL", "TCS", "TECHM", "TITAN", "ULTRACEMCO",
    "UPL", "WIPRO"
]

# NIFTY 500 constituents - Updated January 2025 (fallback list - exactly 500 stocks)
NIFTY500_FALLBACK = [
    "360ONE", "3MINDIA", "ABB", "ACC", "ACMESOLAR", "AIAENG", "APLAPOLLO", "AUBANK",
    "AWL", "AADHARHFC", "AARTIIND", "AAVAS", "ABBOTINDIA", "ACE", "ADANIENSOL", "ADANIENT",
    "ADANIGREEN", "ADANIPORTS", "ADANIPOWER", "ATGL", "ABCAPITAL", "ABFRL", "ABLBL", "ABREL",
    "ABSLAMC", "AEGISLOG", "AEGISVOPAK", "AFCONS", "AFFLE", "AJANTPHARM", "AKUMS", "AKZOINDIA",
    "APLLTD", "ALKEM", "ALKYLAMINE", "ALOKINDS", "ARE&M", "AMBER", "AMBUJACEM", "ANANDRATHI",
    "ANANTRAJ", "ANGELONE", "APARINDS", "APOLLOHOSP", "APOLLOTYRE", "APTUS", "ASAHIINDIA", "ASHOKLEY",
    "ASIANPAINT", "ASTERDM", "ASTRAZEN", "ASTRAL", "ATHERENERG", "ATUL", "AUROPHARMA", "AIIL",
    "DMART", "AXISBANK", "BASF", "BEML", "BLS", "BSE", "BAJAJ-AUTO", "BAJFINANCE",
    "BAJAJFINSV", "BAJAJHLDNG", "BAJAJHFL", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA",
    "MAHABANK", "BATAINDIA", "BAYERCROP", "BERGEPAINT", "BDL", "BEL", "BHARATFORG", "BHEL",
    "BPCL", "BHARTIARTL", "BHARTIHEXA", "BIKAJI", "BIOCON", "BSOFT", "BLUEDART", "BLUEJET",
    "BLUESTARCO", "BBTC", "BOSCHLTD", "FIRSTCRY", "BRIGADE", "BRITANNIA", "MAPMYINDIA", "CCL",
    "CESC", "CGPOWER", "CRISIL", "CAMPUS", "CANFINHOME", "CANBK", "CAPLIPOINT", "CGCL",
    "CARBORUNIV", "CASTROLIND", "CEATLTD", "CENTRALBK", "CDSL", "CENTURYPLY", "CERA", "CHALET",
    "CHAMBLFERT", "CHENNPETRO", "CHOICEIN", "CHOLAHLDNG", "CHOLAFIN", "CIPLA", "CUB", "CLEAN",
    "COALINDIA", "COCHINSHIP", "COFORGE", "COHANCE", "COLPAL", "CAMS", "CONCORDBIO", "CONCOR",
    "COROMANDEL", "CRAFTSMAN", "CREDITACC", "CROMPTON", "CUMMINSIND", "CYIENT", "DCMSHRIRAM", "DLF",
    "DOMS", "DABUR", "DALBHARAT", "DATAPATTNS", "DEEPAKFERT", "DEEPAKNTR", "DELHIVERY", "DEVYANI",
    "DIVISLAB", "DIXON", "AGARWALEYE", "LALPATHLAB", "DRREDDY", "EIDPARRY", "EIHOTEL", "EICHERMOT",
    "ELECON", "ELGIEQUIP", "EMAMILTD", "EMCURE", "ENDURANCE", "ENGINERSIN", "ERIS", "ESCORTS",
    "ETERNAL", "EXIDEIND", "NYKAA", "FEDERALBNK", "FACT", "FINCABLES", "FINPIPE", "FSL",
    "FIVESTAR", "FORCEMOT", "FORTIS", "GAIL", "GVT&D", "GMRAIRPORT", "GRSE", "GICRE",
    "GILLETTE", "GLAND", "GLAXO", "GLENMARK", "MEDANTA", "GODIGIT", "GPIL", "GODFRYPHLP",
    "GODREJAGRO", "GODREJCP", "GODREJIND", "GODREJPROP", "GRANULES", "GRAPHITE", "GRASIM", "GRAVITA",
    "GESHIP", "FLUOROCHEM", "GUJGASLTD", "GMDCLTD", "GSPL", "HEG", "HBLENGINE", "HCLTECH",
    "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL", "HAPPSTMNDS", "HAVELLS", "HEROMOTOCO", "HEXT",
    "HSCL", "HINDALCO", "HAL", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "HINDZINC", "POWERINDIA",
    "HOMEFIRST", "HONASA", "HONAUT", "HUDCO", "HYUNDAI", "ICICIBANK", "ICICIGI", "ICICIPRULI",
    "IDBI", "IDFCFIRSTB", "IFCI", "IIFL", "INOXINDIA", "IRB", "IRCON", "ITCHOTELS",
    "ITC", "ITI", "INDGN", "INDIACEM", "INDIAMART", "INDIANB", "IEX", "INDHOTEL",
    "IOC", "IOB", "IRCTC", "IRFC", "IREDA", "IGL", "INDUSTOWER", "INDUSINDBK",
    "NAUKRI", "INFY", "INOXWIND", "INTELLECT", "INDIGO", "IGIL", "IKS", "IPCALAB",
    "JBCHEPHARM", "JKCEMENT", "JBMA", "JKTYRE", "JMFINANCIL", "JSWENERGY", "JSWINFRA", "JSWSTEEL",
    "JPPOWER", "J&KBANK", "JINDALSAW", "JSL", "JINDALSTEL", "JIOFIN", "JUBLFOOD", "JUBLINGREA",
    "JUBLPHARMA", "JWL", "JYOTHYLAB", "JYOTICNC", "KPRMILL", "KEI", "KPITTECH", "KSB",
    "KAJARIACER", "KPIL", "KALYANKJIL", "KARURVYSYA", "KAYNES", "KEC", "KFINTECH", "KIRLOSBROS",
    "KIRLOSENG", "KOTAKBANK", "KIMS", "LTF", "LTTS", "LICHSGFIN", "LTFOODS", "LTIM",
    "LT", "LATENTVIEW", "LAURUSLABS", "THELEELA", "LEMONTREE", "LICI", "LINDEINDIA", "LLOYDSME",
    "LODHA", "LUPIN", "MMTC", "MRF", "MGL", "MAHSCOOTER", "MAHSEAMLES", "M&MFIN",
    "M&M", "MANAPPURAM", "MRPL", "MANKIND", "MARICO", "MARUTI", "MFSL", "MAXHEALTH",
    "MAZDOCK", "METROPOLIS", "MINDACORP", "MSUMI", "MOTILALOFS", "MPHASIS", "MCX", "MUTHOOTFIN",
    "NATCOPHARM", "NBCC", "NCC", "NHPC", "NLCINDIA", "NMDC", "NSLNISP", "NTPCGREEN",
    "NTPC", "NH", "NATIONALUM", "NAVA", "NAVINFLUOR", "NESTLEIND", "NETWEB", "NEULANDLAB",
    "NEWGEN", "NAM-INDIA", "NIVABUPA", "NUVAMA", "NUVOCO", "OBEROIRLTY", "ONGC", "OIL",
    "OLAELEC", "OLECTRA", "PAYTM", "ONESOURCE", "OFSS", "POLICYBZR", "PCBL", "PGEL",
    "PIIND", "PNBHOUSING", "PTCIL", "PVRINOX", "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET",
    "PFIZER", "PHOENIXLTD", "PIDILITIND", "PPLPHARMA", "POLYMED", "POLYCAB", "POONAWALLA", "PFC",
    "POWERGRID", "PRAJIND", "PREMIERENE", "PRESTIGE", "PGHH", "PNB", "RRKABEL", "RBLBANK",
    "RECLTD", "RHIM", "RITES", "RADICO", "RVNL", "RAILTEL", "RAINBOW", "RKFORGE",
    "RCF", "REDINGTON", "RELIANCE", "RELINFRA", "RPOWER", "SBFC", "SBICARD", "SBILIFE",
    "SJVN", "SKFINDIA", "SRF", "SAGILITY", "SAILIFE", "SAMMAANCAP", "MOTHERSON", "SAPPHIRE",
    "SARDAEN", "SAREGAMA", "SCHAEFFLER", "SCHNEIDER", "SCI", "SHREECEM", "SHRIRAMFIN", "SHYAMMETL",
    "ENRIN", "SIEMENS", "SIGNATURE", "SOBHA", "SOLARINDS", "SONACOMS", "SONATSOFTW", "STARHEALTH",
    "SBIN", "SAIL", "SUMICHEM", "SUNPHARMA", "SUNTV", "SUNDARMFIN", "SUNDRMFAST", "SUPREMEIND",
    "SUZLON", "SWANCORP", "SWIGGY", "SYNGENE", "SYRMA", "TBOTEK", "TVSMOTOR", "TATACHEM",
    "TATACOMM", "TCS", "TATACONSUM", "TATAELXSI", "TATAINVEST", "TMPV", "TATAPOWER", "TATASTEEL",
    "TATATECH", "TTML", "TECHM", "TECHNOE", "TEJASNET", "NIACL", "RAMCOCEM", "THERMAX",
    "TIMKEN", "TITAGARH", "TITAN", "TORNTPHARM", "TORNTPOWER", "TARIL", "TRENT", "TRIDENT",
    "TRIVENI", "TRITURBINE", "TIINDIA", "UCOBANK", "UNOMINDA", "UPL", "UTIAMC", "ULTRACEMCO",
    "UNIONBANK", "UBL", "UNITDSPR", "USHAMART", "VGUARD", "DBREALTY", "VTL", "VBL",
    "MANYAVAR", "VEDL", "VENTIVE", "VIJAYA", "VMM", "IDEA", "VOLTAS", "WAAREEENER",
    "WELCORP", "WELSPUNLIV", "WHIRLPOOL", "WIPRO", "WOCKPHARMA", "YESBANK", "ZFCVINDIA", "ZEEL",
    "ZENTEC", "ZENSARTECH", "ZYDUSLIFE", "ECLERX",
]

IST = timezone(timedelta(hours=5, minutes=30))

# Server-side heartbeat to keep application alive
heartbeat_active = True
PREVIEW_URL = os.environ.get('PREVIEW_URL', 'https://90cce107-f4b8-429a-a437-e87f6922864b.preview.emergentagent.com')

def heartbeat_thread():
    """Background thread to keep server active with periodic self-ping"""
    logger.info("Heartbeat thread started - will ping every 3 minutes to keep server alive")
    logger.info(f"Heartbeat will ping: localhost:8001 AND {PREVIEW_URL}")
    
    while heartbeat_active:
        try:
            time.sleep(180)  # Sleep for 3 minutes
            
            # Ping 1: Internal localhost ping
            try:
                response = requests.get("http://localhost:8001/api/health", timeout=10)
                if response.status_code == 200:
                    logger.info("✓ Heartbeat: Internal localhost ping successful")
            except Exception as e:
                logger.warning(f"Heartbeat internal ping failed: {e}")
            
            # Ping 2: External preview URL ping (CRITICAL for keeping preview alive)
            try:
                external_url = f"{PREVIEW_URL}/api/health"
                response = requests.get(external_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✓ Heartbeat: External preview URL ping successful - {PREVIEW_URL}")
            except Exception as e:
                logger.warning(f"Heartbeat external ping failed (may be normal during startup): {e}")
                
        except Exception as e:
            logger.error(f"Heartbeat thread error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying on error

# Start heartbeat thread
heartbeat_bg_thread = threading.Thread(target=heartbeat_thread, daemon=True)
heartbeat_bg_thread.start()
logger.info("Server heartbeat initiated - application will remain active independently")
logger.info("Heartbeat pings BOTH localhost AND external preview URL every 3 minutes")


def get_ist_now():
    return datetime.now(IST)

def is_nifty_index(symbol: str) -> bool:
    """Check if symbol is a NIFTY index (not a stock)"""
    if not symbol:
        return False
    symbol_clean = symbol.upper().replace(" ", "").replace("-", "")
    nifty_patterns = ["NIFTY500", "NIFTY200", "NIFTY50", "NIFTYJR", "NIFTYMIDCAP", "NIFTYBANK"]
    for pattern in nifty_patterns:
        if pattern in symbol_clean:
            return True
    return False

def is_cache_valid(timestamp, max_age_minutes):
    if timestamp is None:
        return False
    return (get_ist_now() - timestamp).total_seconds() < max_age_minutes * 60

def is_market_currently_open() -> bool:
    """Check if market is currently open (Mon-Fri, 9:15 AM - 3:30 PM IST)"""
    now = datetime.now(IST)
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    # Check if it's a weekday
    if weekday not in [0, 1, 2, 3, 4]:  # Not Monday-Friday
        return False
    
    # Check if it's within trading hours (9:15 AM - 3:30 PM)
    if (hour > 9 or (hour == 9 and minute >= 15)) and (hour < 15 or (hour == 15 and minute < 30)):
        return True
    
    return False

def is_valid_symbol(symbol: str) -> bool:
    """Check if symbol is valid (not dummy, not index, not empty)"""
    if not symbol or not symbol.strip():
        return False
    
    symbol_clean = symbol.upper().strip()
    
    if 'DUMMY' in symbol_clean or 'TEST' in symbol_clean:
        return False
    
    if is_nifty_index(symbol_clean):
        return False
    
    return True

# Database helper functions are now in database.py module

def fetch_nifty50_from_csv():
    """Fetch NIFTY 50 list from NSE CSV"""
    try:
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/csv,application/csv,text/plain',
        }
        
        logger.info(f"Fetching NIFTY 50 from CSV: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            csv_content = StringIO(response.text)
            csv_reader = csv.DictReader(csv_content)
            
            symbols = []
            for row in csv_reader:
                symbol = row.get('Symbol', '').strip()
                if is_valid_symbol(symbol):
                    symbols.append(symbol)
            
            logger.info(f"Fetched {len(symbols)} valid stocks from NSE CSV for NIFTY 50")
            
            if len(symbols) >= 50:
                symbols = symbols[:50]
                logger.info(f"Returning exactly 50 NIFTY50 stocks from CSV")
                return symbols
            else:
                logger.warning(f"Only {len(symbols)} valid stocks in CSV, need 50 - using fallback")
                return None
        else:
            logger.warning(f"Failed to fetch NIFTY 50 CSV: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.warning(f"Could not fetch NIFTY 50 from CSV: {e}")
        return None

def fetch_nifty500_from_csv():
    """Fetch NIFTY 500 list from NSE CSV"""
    try:
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/csv,application/csv,text/plain',
        }
        
        logger.info(f"Fetching NIFTY 500 from CSV: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            csv_content = StringIO(response.text)
            csv_reader = csv.DictReader(csv_content)
            
            symbols = []
            for row in csv_reader:
                symbol = row.get('Symbol', '').strip()
                if is_valid_symbol(symbol):
                    symbols.append(symbol)
            
            logger.info(f"Fetched {len(symbols)} valid stocks from NSE CSV for NIFTY 500")
            
            if len(symbols) >= 500:
                symbols = symbols[:500]
                logger.info(f"Returning exactly 500 NIFTY500 stocks from CSV")
                return symbols
            else:
                logger.warning(f"Only {len(symbols)} valid stocks in CSV, need 500 - using fallback")
                return None
        else:
            logger.warning(f"Failed to fetch NIFTY 500 CSV: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.warning(f"Could not fetch NIFTY 500 from CSV: {e}")
        return None

def fetch_nifty500_from_nse():
    """Try to fetch NIFTY 500 list from NSE website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            symbols = [item['symbol'] for item in data.get('data', []) if not is_nifty_index(item['symbol']) and is_valid_symbol(item['symbol'])]
            if len(symbols) >= 50:
                logger.info(f"Fetched {len(symbols)} stocks from NSE for NIFTY 500")
                return symbols
    except Exception as e:
        logger.warning(f"Could not fetch NIFTY 500 from NSE: {e}")
    return None

def get_nifty50_symbols():
    """Fetch NIFTY 50 constituents with fallback"""
    # Check Supabase first
    cached = get_stock_list('nifty50', 1440)
    if cached:
        logger.info("Using NIFTY 50 from Supabase cache")
        return cached

    # Check in-memory cache
    with cache_lock:
        if is_cache_valid(cache["nifty50_list"]["timestamp"], 1440):
            return cache["nifty50_list"]["data"]

    # Try NSE CSV first
    symbols = fetch_nifty50_from_csv()
    if symbols and len(symbols) == 50:
        save_stock_list('nifty50', symbols)
        with cache_lock:
            cache["nifty50_list"] = {"data": symbols, "timestamp": get_ist_now()}
        logger.info("Using NIFTY 50 from NSE CSV")
        return symbols

    # Fallback to hardcoded list
    logger.info("Using NIFTY 50 fallback list")
    save_stock_list('nifty50', NIFTY50_SYMBOLS)
    with cache_lock:
        cache["nifty50_list"] = {"data": NIFTY50_SYMBOLS, "timestamp": get_ist_now()}
    return NIFTY50_SYMBOLS

def get_nifty500_symbols():
    """Fetch NIFTY 500 constituents with fallback"""
    # Check Supabase first
    cached = get_stock_list('nifty500', 1440)
    if cached:
        logger.info("Using NIFTY 500 from Supabase cache")
        return cached

    # Check in-memory cache
    with cache_lock:
        if is_cache_valid(cache["nifty500_list"]["timestamp"], 1440):
            return cache["nifty500_list"]["data"]

    # Try NSE CSV first
    symbols = fetch_nifty500_from_csv()
    if symbols and len(symbols) == 500:
        save_stock_list('nifty500', symbols)
        with cache_lock:
            cache["nifty500_list"] = {"data": symbols, "timestamp": get_ist_now()}
        logger.info("Using NIFTY 500 from NSE CSV")
        return symbols

    # Try NSE API as secondary option
    symbols = fetch_nifty500_from_nse()
    if symbols:
        symbols = [s for s in symbols if not is_nifty_index(s) and is_valid_symbol(s)]
        save_stock_list('nifty500', symbols)
        with cache_lock:
            cache["nifty500_list"] = {"data": symbols, "timestamp": get_ist_now()}
        logger.info("Using NIFTY 500 from NSE API")
        return symbols

    # Fallback to hardcoded list
    logger.info("Using NIFTY 500 fallback list")
    save_stock_list('nifty500', NIFTY500_FALLBACK)
    with cache_lock:
        cache["nifty500_list"] = {"data": NIFTY500_FALLBACK, "timestamp": get_ist_now()}
    return NIFTY500_FALLBACK

def get_yf_symbol(symbol):
    return f"{symbol}.NS"

def get_ohlc_data(symbol: str, timeframe: str, retry_count: int = 0, max_retries: int = 5):
    """Fetch OHLC data with Supabase and in-memory caching, with retry logic for rate limits"""
    cache_key = f"{symbol}_{timeframe}"

    # Check Supabase first with extended validity during rate limit periods
    # Check for recent cache first (15 min), then try older cache (24 hours) as fallback
    cached = get_ohlc_cache(symbol, timeframe, 15)
    if cached:
        return cached

    # Try older cache (24 hours) as fallback for rate limit scenarios
    cached_old = get_ohlc_cache(symbol, timeframe, 1440)

    # Check in-memory cache
    with cache_lock:
        if cache_key in cache["ohlc"] and is_cache_valid(cache["ohlc"][cache_key]["timestamp"], 15):
            return cache["ohlc"][cache_key]["data"]

    try:
        yf_symbol = get_yf_symbol(symbol)
        ticker = yf.Ticker(yf_symbol)

        if timeframe == "monthly":
            df = ticker.history(period="3y", interval="1mo")
        elif timeframe == "weekly":
            df = ticker.history(period="1y", interval="1wk")
        elif timeframe == "daily":
            df = ticker.history(period="3mo", interval="1d")
        elif timeframe == "1hour":
            df = ticker.history(period="30d", interval="1h")
        elif timeframe == "15min":
            df = ticker.history(period="5d", interval="15m")
        else:
            return []

        if df.empty:
            # If fetch failed but we have old cache, use it
            if cached_old:
                logger.info(f"Using stale cache for {symbol} {timeframe} due to empty response")
                return cached_old
            return []

        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "timestamp": idx.isoformat(),
                "open": round(float(row["Open"]), 2),
                "close": round(float(row["Close"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2)
            })

        # Save to both Supabase and in-memory cache
        save_ohlc_cache(symbol, timeframe, candles)
        with cache_lock:
            cache["ohlc"][cache_key] = {"data": candles, "timestamp": get_ist_now()}

        return candles
    except Exception as e:
        error_msg = str(e)
        # If rate limited, retry with exponential backoff
        if ("Too Many Requests" in error_msg or "Rate limit" in error_msg) and retry_count < max_retries:
            wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30 seconds
            logger.warning(f"Rate limited for {symbol} {timeframe}, retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
            time.sleep(wait_time)
            return get_ohlc_data(symbol, timeframe, retry_count + 1, max_retries)
        elif "Too Many Requests" in error_msg or "Rate limit" in error_msg:
            if cached_old:
                logger.info(f"Using stale cache for {symbol} {timeframe} after max retries")
                return cached_old
            logger.error(f"Rate limited for {symbol} {timeframe}, max retries exceeded, no cache available")
        else:
            logger.error(f"Error fetching OHLC for {symbol} {timeframe}: {e}")
        return []

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def get_in_scope_candles(candles: List[Dict], timeframe: str) -> List[Dict]:
    """Filter candles based on in-scope rules"""
    if not candles:
        return []
    
    now = get_ist_now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    # Check if market is currently closed (before open or after close on weekdays, or weekend)
    market_closed = False
    if weekday in [0, 1, 2, 3, 4]:  # Monday to Friday
        if (hour < 9 or (hour == 9 and minute < 15)) or (hour > 15 or (hour == 15 and minute >= 30)):
            market_closed = True
    elif weekday in [5, 6]:  # Weekend
        market_closed = True
    
    if timeframe in ["daily", "1hour", "15min"]:
        # For intraday timeframes, if market is closed, include the last candle (it's complete)
        # If market is open, exclude the last candle (it's forming)
        if not market_closed:
            return candles[:-1] if len(candles) > 1 else []
        return candles
    
    elif timeframe == "monthly":
        if not candles:
            return candles
        
        try:
            last_candle = candles[-1]
            last_candle_date = datetime.fromisoformat(last_candle["timestamp"].replace('Z', '+00:00'))
            last_candle_date_ist = last_candle_date.astimezone(IST)
            
            # Check if last candle is from previous month or current month
            last_candle_month = last_candle_date_ist.month
            last_candle_year = last_candle_date_ist.year
            current_month = now.month
            current_year = now.year
            
            # If last candle is from a previous month (different month or year), it's complete - include it
            if last_candle_year < current_year or (last_candle_year == current_year and last_candle_month < current_month):
                return candles
            
            # Last candle is from current month - check if >80% of month has passed
            # A month is >80% complete when day >= 24 (24/30 = 80%, 24/31 = 77%)
            day_of_month = now.day
            if day_of_month >= 24:
                return candles
            else:
                # Current month not yet 80% complete, exclude the forming candle
                return candles[:-1] if len(candles) > 1 else []
                
        except Exception as e:
            logger.warning(f"Error parsing monthly candle date: {e}")
            # Fallback to old simple logic
            day_of_month = now.day
            if day_of_month >= 24:
                return candles
            else:
                return candles[:-1] if len(candles) > 1 else []
    
    elif timeframe == "weekly":
        if not candles:
            return []
        
        try:
            last_candle = candles[-1]
            last_candle_date = datetime.fromisoformat(last_candle["timestamp"].replace('Z', '+00:00'))
            last_candle_date_ist = last_candle_date.astimezone(IST)
            
            # Get the start of current week (Monday)
            current_week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            days_since_monday = now.weekday()
            current_week_start = current_week_start - timedelta(days=days_since_monday)
            
            # If last candle is from a previous week, include it (it's complete)
            if last_candle_date_ist < current_week_start:
                return candles
            
            # Last candle is from current week - apply specific inclusion rules
            # INCLUDE last weekly candle IF:
            # 1. Thursday after 3:30PM (market closed) OR
            # 2. Friday, Saturday, or Sunday (any time) OR
            # 3. Monday before 9:15AM (specifically)
            if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday - always include
                return candles
            elif weekday == 3 and market_closed:  # Thursday after 3:30PM - include
                return candles
            elif weekday == 0 and (hour < 9 or (hour == 9 and minute < 15)):  # Monday before 9:15AM - include
                return candles
            else:
                # All other cases - exclude the forming candle
                return candles[:-1] if len(candles) > 1 else []
                
        except Exception as e:
            logger.warning(f"Error parsing weekly candle date: {e}")
            # Fallback logic with same rules
            if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
                return candles
            elif weekday == 3 and market_closed:  # Thursday after 3:30PM
                return candles
            elif weekday == 0 and (hour < 9 or (hour == 9 and minute < 15)):  # Monday before 9:15AM
                return candles
            else:
                return candles[:-1] if len(candles) > 1 else []
    
    return candles

def calculate_udts(candles: List[Dict]) -> Dict:
    """Calculate UDTS direction and return G1, R1, R2, G2 candles"""
    if not candles:
        return {"direction": "UNKNOWN", "g1": None, "r1": None, "r2": None, "g2": None}
    
    g1_idx = None
    r1_idx = None
    
    for i in range(len(candles) - 1, -1, -1):
        if is_green(candles[i]):
            for j in range(i - 1, -1, -1):
                if is_red(candles[j]):
                    if candles[i]["close"] > candles[j]["open"]:
                        g1_idx = i
                        r1_idx = j
                    break
            if g1_idx is not None:
                break
    
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
    
    r2_idx = None
    g2_idx = None
    
    for i in range(g1_idx + 1, len(candles)):
        if is_red(candles[i]):
            for j in range(i - 1, -1, -1):
                if is_green(candles[j]):
                    if candles[i]["close"] < candles[j]["open"]:
                        r2_idx = i
                        g2_idx = j
                    break
            if r2_idx is not None:
                break
    
    direction = "DOWN" if r2_idx is not None else "UP"
    
    return {
        "direction": direction,
        "g1": candles[g1_idx] if g1_idx is not None else None,
        "r1": candles[r1_idx] if r1_idx is not None else None,
        "r2": candles[r2_idx] if r2_idx is not None else None,
        "g2": candles[g2_idx] if g2_idx is not None else None
    }

def get_support_price(candles: List[Dict], direction: str) -> Optional[float]:
    """Get support price"""
    if not candles:
        return None
    
    for i in range(len(candles) - 1, -1, -1):
        if direction == "UP" and is_green(candles[i]):
            return candles[i]["open"]
        elif direction == "DOWN" and is_red(candles[i]):
            return candles[i]["open"]
    return None

def get_9_15_to_9_30_candle(candles: List[Dict]) -> Optional[Dict]:
    """Find the most recent 15-min candle for 9:15-9:30 IST"""
    if not candles:
        return None
    
    for candle in reversed(candles):
        try:
            timestamp = datetime.fromisoformat(candle["timestamp"].replace('Z', '+00:00'))
            timestamp_ist = timestamp.astimezone(IST)
            
            if timestamp_ist.hour == 9 and timestamp_ist.minute == 15:
                return candle
        except Exception as e:
            logger.warning(f"Error parsing candle timestamp: {e}")
            continue
    
    return None


def get_todays_session_candles(candles: List[Dict]) -> List[Dict]:
    """
    Get all candles from today's trading session (if market open) 
    or last trading session (if market closed)
    """
    if not candles:
        return []
    
    # Get current IST time
    now = datetime.now(IST)
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    # Check if market is currently open
    market_open = False
    if weekday in [0, 1, 2, 3, 4]:  # Monday to Friday
        if (hour > 9 or (hour == 9 and minute >= 15)) and (hour < 15 or (hour == 15 and minute < 30)):
            market_open = True
    
    # Filter candles for today's or last session
    session_candles = []
    
    if market_open:
        # Market is open - get today's candles (from 9:15 AM today onwards)
        for candle in candles:
            try:
                timestamp = datetime.fromisoformat(candle["timestamp"].replace('Z', '+00:00'))
                timestamp_ist = timestamp.astimezone(IST)
                
                if (timestamp_ist.year == now.year and 
                    timestamp_ist.month == now.month and 
                    timestamp_ist.day == now.day and
                    timestamp_ist.hour >= 9):
                    session_candles.append(candle)
            except Exception as e:
                logger.warning(f"Error parsing candle timestamp: {e}")
                continue
    else:
        # Market is closed - get LAST (most recent) trading session's candles
        # Iterate in REVERSE to find the most recent session
        for candle in reversed(candles):
            try:
                timestamp = datetime.fromisoformat(candle["timestamp"].replace('Z', '+00:00'))
                timestamp_ist = timestamp.astimezone(IST)
                
                if session_candles:
                    # Already have some candles, check if this is from same session
                    first_ts = datetime.fromisoformat(session_candles[0]["timestamp"].replace('Z', '+00:00')).astimezone(IST)
                    if (timestamp_ist.year == first_ts.year and 
                        timestamp_ist.month == first_ts.month and 
                        timestamp_ist.day == first_ts.day):
                        session_candles.insert(0, candle)  # Insert at beginning to maintain order
                    else:
                        # Different day, stop collecting
                        break
                else:
                    # This is the first (most recent) candle - start collecting from this day
                    session_candles.append(candle)
            except Exception as e:
                logger.warning(f"Error parsing candle timestamp: {e}")
                continue
    
    return session_candles

def get_latest_closed_candles(candles: List[Dict], min_count: int = 24) -> List[Dict]:
    """Get latest closed candles"""
    if not candles:
        return []
    closed = candles[:-1] if len(candles) > 1 else candles
    return closed[-min_count:] if len(closed) > min_count else closed

def calculate_15min_blocks(candles: List[Dict]) -> List[Dict]:
    """
    Partition candles into blocks using simplified logic for 15-min biggest trend.
    
    Logic:
    1. Start with first candle color - determines first block direction
    2. Same color candles continue the same block
    3. Opposite color candle triggers trend change check:
       - If previous is GREEN and current is RED: check if RED close < GREEN open
       - If previous is RED and current is GREEN: check if GREEN close > RED open
       - If condition met: trend changes, new block starts
       - If condition not met: continue same block
    4. Calculate power for each block as max - min of all opens/closes
    """
    if not candles or len(candles) < 1:
        return []
    
    blocks = []
    current_block = [candles[0]]
    current_direction = "UP" if is_green(candles[0]) else "DOWN"
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        previous_color = "GREEN" if is_green(previous_candle) else "RED"
        
        # Check if candle color matches current block direction
        if current_direction == "UP" and current_color == "GREEN":
            # Same color, continue block
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            # Same color, continue block
            current_block.append(current_candle)
        else:
            # Opposite color - check if trend actually changes
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                # Was UP (previous GREEN), now RED - check if RED close < GREEN open
                if current_candle["close"] < previous_candle["open"]:
                    trend_changed = True
            elif current_direction == "DOWN" and current_color == "GREEN":
                # Was DOWN (previous RED), now GREEN - check if GREEN close > RED open
                if current_candle["close"] > previous_candle["open"]:
                    trend_changed = True
            
            if trend_changed:
                # Save current block
                block_opens_closes = []
                for c in current_block:
                    block_opens_closes.extend([c["open"], c["close"]])
                
                if block_opens_closes:
                    blocks.append({
                        "candles": current_block.copy(),
                        "direction": current_direction,
                        "power": max(block_opens_closes) - min(block_opens_closes),
                        "start_price": current_block[0]["open"],
                        "low": min(block_opens_closes),
                        "high": max(block_opens_closes)
                    })
                
                # Start new block
                current_block = [current_candle]
                current_direction = "UP" if current_color == "GREEN" else "DOWN"
            else:
                # No trend change, continue same block
                current_block.append(current_candle)
    
    # Save the last block
    if current_block:
        block_opens_closes = []
        for c in current_block:
            block_opens_closes.extend([c["open"], c["close"]])
        
        if block_opens_closes:
            blocks.append({
                "candles": current_block,
                "direction": current_direction,
                "power": max(block_opens_closes) - min(block_opens_closes),
                "start_price": current_block[0]["open"],
                "low": min(block_opens_closes),
                "high": max(block_opens_closes)
            })
    
    return blocks

def get_biggest_trend(blocks: List[Dict]) -> Optional[Dict]:
    """Get block with maximum power (first occurrence from left to right)"""
    if not blocks:
        return None
    
    max_power = max(b["power"] for b in blocks)
    # Return the FIRST block with max power (left to right on chart)
    for b in blocks:
        if b["power"] == max_power:
            # Add start and end candle details
            candles = b.get("candles", [])
            if candles:
                start_candle = candles[0]
                end_candle = candles[-1]
                b["start_candle"] = {
                    "datetime": start_candle.get("timestamp"),  # Fixed: was "datetime", should be "timestamp"
                    "open": start_candle.get("open"),
                    "close": start_candle.get("close")
                }
                b["end_candle"] = {
                    "datetime": end_candle.get("timestamp"),  # Fixed: was "datetime", should be "timestamp"
                    "open": end_candle.get("open"),
                    "close": end_candle.get("close")
                }
            return b
    return blocks[0]

def get_institutional_holding_percentage(symbol: str) -> str:
    """Get absolute % of shares held by institutional investors"""
    # Check Supabase first
    cached = get_institutional_cache(symbol, 129600)
    if cached:
        return cached

    # Check in-memory cache
    with cache_lock:
        if symbol in cache["institutional_holdings"] and is_cache_valid(
            cache["institutional_holdings"][symbol]["timestamp"], 129600
        ):
            return cache["institutional_holdings"][symbol]["data"]

    try:
        ticker = yf.Ticker(get_yf_symbol(symbol))

        try:
            info = ticker.info
            held_pct = info.get('heldPercentInstitutions', None)

            if held_pct is not None:
                pct_value = held_pct * 100
                result = f"{pct_value:.2f}"

                save_institutional_cache(symbol, result)
                with cache_lock:
                    cache["institutional_holdings"][symbol] = {
                        "data": result,
                        "timestamp": get_ist_now()
                    }

                logger.info(f"{symbol}: Institutional holding = {result}% (Method 1)")
                return result
        except Exception as e:
            logger.warning(f"{symbol}: Could not use info['heldPercentInstitutions']: {e}")

        try:
            major_holders = ticker.major_holders

            if major_holders is not None and not major_holders.empty:
                for idx, row in major_holders.iterrows():
                    desc = str(row[1]) if len(row) > 1 else ""
                    if "Institutions" in desc or "institutions" in desc:
                        pct_str = str(row[0]).replace('%', '').strip()
                        try:
                            pct_value = float(pct_str)
                            result = f"{pct_value:.2f}"

                            save_institutional_cache(symbol, result)
                            with cache_lock:
                                cache["institutional_holdings"][symbol] = {
                                    "data": result,
                                    "timestamp": get_ist_now()
                                }

                            logger.info(f"{symbol}: Institutional holding = {result}% (Method 2)")
                            return result
                        except ValueError:
                            pass
        except Exception as e:
            logger.warning(f"{symbol}: Could not use major_holders: {e}")

        result = "NA"
        save_institutional_cache(symbol, result)
        with cache_lock:
            cache["institutional_holdings"][symbol] = {
                "data": result,
                "timestamp": get_ist_now()
            }

        logger.info(f"{symbol}: Institutional holdings data not available")
        return result

    except Exception as e:
        logger.error(f"{symbol}: Error fetching institutional holding: {e}")
        result = "NA"

        save_institutional_cache(symbol, result)
        with cache_lock:
            cache["institutional_holdings"][symbol] = {
                "data": result,
                "timestamp": get_ist_now()
            }

        return result

def get_fundamentals(symbol: str, retry_count: int = 0, max_retries: int = 5) -> Dict:
    """Fetch fundamental data with Supabase and in-memory caching, with retry logic for rate limits"""
    # Check Supabase first (24 hours validity)
    cached = get_fundamentals_cache(symbol, 1440)
    if cached:
        return cached

    # Try older cache (7 days) as fallback
    cached_old = get_fundamentals_cache(symbol, 10080)

    # Check in-memory cache
    with cache_lock:
        if symbol in cache["fundamentals"] and is_cache_valid(cache["fundamentals"][symbol]["timestamp"], 1440):
            return cache["fundamentals"][symbol]["data"]

    try:
        ticker = yf.Ticker(get_yf_symbol(symbol))
        info = ticker.info

        sector = info.get("sector", None)
        industry = info.get("industry", None)
        inst_holding_pct = get_institutional_holding_percentage(symbol)

        # Get analyst count
        analyst_count = info.get("numberOfAnalystOpinions", None)

        fundamentals = {
            "sector": sector,
            "industry": industry,
            "roe": info.get("returnOnEquity", None),
            "pe": info.get("trailingPE", None),
            "pb": info.get("priceToBook", None),
            "de": info.get("debtToEquity", None),
            "revenue_growth": info.get("revenueGrowth", None),
            "earnings_growth": info.get("earningsGrowth", None),
            "target_price": info.get("targetMeanPrice", None),
            "inst_holding_pct": inst_holding_pct,
            "analyst_count": analyst_count,
            "dividend_yield": info.get("dividendYield", None),
            "net_income_to_common": info.get("netIncomeToCommon", None),
            "enterprise_to_ebitda": info.get("enterpriseToEbitda", None),
            "enterprise_to_revenue": info.get("enterpriseToRevenue", None)
        }

        if fundamentals["roe"] is not None:
            fundamentals["roe"] = round(fundamentals["roe"] * 100, 0)
        if fundamentals["revenue_growth"] is not None:
            fundamentals["revenue_growth"] = round(fundamentals["revenue_growth"] * 100, 0)
        if fundamentals["earnings_growth"] is not None:
            fundamentals["earnings_growth"] = round(fundamentals["earnings_growth"] * 100, 0)
        if fundamentals["pe"] is not None:
            fundamentals["pe"] = round(fundamentals["pe"], 0)
        if fundamentals["pb"] is not None:
            fundamentals["pb"] = round(fundamentals["pb"], 1)
        if fundamentals["de"] is not None:
            fundamentals["de"] = round(fundamentals["de"], 0)

        # Format new fields
        if fundamentals["dividend_yield"] is not None:
            fundamentals["dividend_yield"] = round(fundamentals["dividend_yield"] * 100, 2)
        if fundamentals["net_income_to_common"] is not None:
            # Convert to Rs Crores (divide by 10^7)
            fundamentals["net_income_to_common"] = round(fundamentals["net_income_to_common"] / 1e7, 2)
        if fundamentals["enterprise_to_ebitda"] is not None:
            fundamentals["enterprise_to_ebitda"] = round(fundamentals["enterprise_to_ebitda"], 2)
        if fundamentals["enterprise_to_revenue"] is not None:
            fundamentals["enterprise_to_revenue"] = round(fundamentals["enterprise_to_revenue"], 2)

        market_cap = info.get("marketCap", None)
        if market_cap is not None:
            fundamentals["market_cap_tkc"] = round(market_cap / 1e10, 0)
        else:
            fundamentals["market_cap_tkc"] = None

        save_fundamentals_cache(symbol, fundamentals)
        with cache_lock:
            cache["fundamentals"][symbol] = {"data": fundamentals, "timestamp": get_ist_now()}

        return fundamentals
    except Exception as e:
        error_msg = str(e)
        # If rate limited, retry with exponential backoff
        if ("Too Many Requests" in error_msg or "Rate limit" in error_msg) and retry_count < max_retries:
            wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30 seconds
            logger.warning(f"Rate limited for {symbol} fundamentals, retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
            time.sleep(wait_time)
            return get_fundamentals(symbol, retry_count + 1, max_retries)
        elif "Too Many Requests" in error_msg or "Rate limit" in error_msg:
            if cached_old:
                logger.info(f"Using stale cache for {symbol} fundamentals after max retries")
                return cached_old
            logger.error(f"Rate limited for {symbol} fundamentals, max retries exceeded, no cache available")
        else:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
        return {}


def calculate_rsi(candles: List[Dict], period: int = 14) -> Optional[float]:
    """Calculate RSI (Relative Strength Index) for the latest candle"""
    try:
        if not candles or len(candles) < period + 1:
            return None
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(candles)
        if 'close' not in df.columns or df['close'].isna().all():
            return None
        
        # Calculate RSI using ta library
        rsi_series = ta.momentum.RSIIndicator(close=df['close'], window=period).rsi()
        
        # Get the last RSI value
        if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]):
            return round(float(rsi_series.iloc[-1]), 2)
        return None
    except Exception as e:
        logger.warning(f"Error calculating RSI: {e}")
        return None

def calculate_adx(candles: List[Dict], period: int = 14) -> Optional[float]:
    """Calculate ADX (Average Directional Index) for the latest candle"""
    try:
        if not candles or len(candles) < period + 1:
            return None
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(candles)
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None
        if df[required_cols].isna().all().any():
            return None
        
        # Calculate ADX using ta library
        adx_series = ta.trend.ADXIndicator(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            window=period
        ).adx()
        
        # Get the last ADX value
        if not adx_series.empty and not pd.isna(adx_series.iloc[-1]):
            return round(float(adx_series.iloc[-1]), 2)
        return None
    except Exception as e:
        logger.warning(f"Error calculating ADX: {e}")
        return None

def calculate_supertrend(candles: List[Dict], atr_period: int = 10, multiplier: float = 3.0) -> Optional[Dict]:
    """Calculate Supertrend indicator for the latest candle"""
    try:
        if not candles or len(candles) < atr_period + 1:
            return None
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(candles)
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None
        if df[required_cols].isna().all().any():
            return None
        
        # Calculate ATR
        atr = ta.volatility.AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=atr_period
        ).average_true_range()
        
        # Calculate basic bands
        hl_avg = (df['high'] + df['low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize supertrend
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=str)
        
        # First valid supertrend value
        first_valid_idx = atr.first_valid_index()
        if first_valid_idx is None:
            return None
        
        supertrend.iloc[first_valid_idx] = lower_band.iloc[first_valid_idx]
        direction.iloc[first_valid_idx] = 'UP'
        
        # Calculate supertrend for rest of the data
        for i in range(first_valid_idx + 1, len(df)):
            prev_supertrend = supertrend.iloc[i-1]
            prev_direction = direction.iloc[i-1]
            curr_close = df['close'].iloc[i]
            curr_lower = lower_band.iloc[i]
            curr_upper = upper_band.iloc[i]
            
            if pd.isna(prev_supertrend):
                supertrend.iloc[i] = curr_lower
                direction.iloc[i] = 'UP'
                continue
            
            # Update bands based on previous supertrend
            if curr_lower > prev_supertrend:
                final_lower = curr_lower
            else:
                final_lower = prev_supertrend if prev_direction == 'UP' else curr_lower
                
            if curr_upper < prev_supertrend:
                final_upper = curr_upper
            else:
                final_upper = prev_supertrend if prev_direction == 'DOWN' else curr_upper
            
            # Determine direction
            if prev_direction == 'UP':
                if curr_close <= final_lower:
                    supertrend.iloc[i] = final_upper
                    direction.iloc[i] = 'DOWN'
                else:
                    supertrend.iloc[i] = final_lower
                    direction.iloc[i] = 'UP'
            else:  # prev_direction == 'DOWN'
                if curr_close >= final_upper:
                    supertrend.iloc[i] = final_lower
                    direction.iloc[i] = 'UP'
                else:
                    supertrend.iloc[i] = final_upper
                    direction.iloc[i] = 'DOWN'
        
        # Get last values
        last_close = df['close'].iloc[-1]
        last_supertrend = supertrend.iloc[-1]
        last_direction = direction.iloc[-1]
        
        if pd.isna(last_supertrend) or pd.isna(last_close):
            return None
        
        # Determine if price is above or below supertrend
        if last_close > last_supertrend:
            trend = "UP"
        else:
            trend = "DOWN"
        
        return {
            "direction": trend,
            "level": round(float(last_supertrend), 2)
        }
    except Exception as e:
        logger.warning(f"Error calculating Supertrend: {e}")
        return None

def calculate_bollinger_bands_pct(candles: List[Dict], period: int = 20, std_dev: float = 2.0) -> Optional[float]:
    """Calculate Bollinger Bands %B for the latest candle
    %B = ((close - lower_band) / (upper_band - lower_band)) * 100
    """
    try:
        if not candles or len(candles) < period:
            return None
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(candles)
        if 'close' not in df.columns or df['close'].isna().all():
            return None
        
        # Calculate Bollinger Bands using ta library
        bb = ta.volatility.BollingerBands(close=df['close'], window=period, window_dev=std_dev)
        upper_band = bb.bollinger_hband()
        lower_band = bb.bollinger_lband()
        
        # Get last values
        last_close = df['close'].iloc[-1]
        last_upper = upper_band.iloc[-1]
        last_lower = lower_band.iloc[-1]
        
        if pd.isna(last_close) or pd.isna(last_upper) or pd.isna(last_lower):
            return None
        
        # Avoid division by zero
        band_width = last_upper - last_lower
        if band_width == 0:
            return None
        
        # Calculate %B
        pct_b = ((last_close - last_lower) / band_width) * 100
        return round(float(pct_b), 2)
    except Exception as e:
        logger.warning(f"Error calculating Bollinger Bands %B: {e}")
        return None

def analyze_stock(symbol: str) -> Dict:
    """Full analysis for a single stock"""
    result = {"symbol": symbol, "error": None}
    
    try:
        timeframes = ["monthly", "weekly", "daily", "1hour", "15min"]
        ohlc_data = {}
        udts_results = {}
        support_prices = {}
        
        for tf in timeframes:
            candles = get_ohlc_data(symbol, tf)
            in_scope = get_in_scope_candles(candles, tf)
            ohlc_data[tf] = in_scope
            udts_result = calculate_udts(in_scope)
            udts_results[tf] = udts_result
        
        fundamentals = get_fundamentals(symbol)
        analyst_count = fundamentals.get("analyst_count")
        
        # Get ALL daily candles (not in-scope) to calculate CMP and CMP change
        all_daily_candles = get_ohlc_data(symbol, "daily")
        
        # CMP is the last candle's close price (whether forming or complete)
        cmp = None
        cmp_change_pct = None
        previous_close = None
        
        if all_daily_candles and len(all_daily_candles) >= 1:
            cmp = all_daily_candles[-1]["close"]
        
        if all_daily_candles and len(all_daily_candles) >= 2:
            latest_close = all_daily_candles[-1]["close"]
            previous_close = all_daily_candles[-2]["close"]
            
            # Calculate CMP change percentage: how much % the latest close changed from previous close
            if latest_close and previous_close and previous_close > 0:
                cmp_change_pct = round(((latest_close - previous_close) / previous_close) * 100, 2)
        
        # Calculate 2yr high % from monthly chart
        # Get ALL monthly candles (including last candle, even if not in scope)
        all_monthly_candles = get_ohlc_data(symbol, "monthly")
        two_yr_high_pct = None
        
        if all_monthly_candles and len(all_monthly_candles) >= 1:
            # Find highest open or close price in ALL monthly candles
            all_monthly_prices = []
            for candle in all_monthly_candles:
                if candle.get("open") is not None:
                    all_monthly_prices.append(candle["open"])
                if candle.get("close") is not None:
                    all_monthly_prices.append(candle["close"])
            
            if all_monthly_prices:
                highest_monthly_price = max(all_monthly_prices)
                last_monthly_close = all_monthly_candles[-1].get("close")
                
                if last_monthly_close and last_monthly_close > 0:
                    two_yr_high_pct = round(((highest_monthly_price / last_monthly_close) - 1) * 100, 2)
        
        is_triple_up = all(udts_results[tf]["direction"] == "UP" for tf in ["monthly", "weekly", "daily"])
        is_triple_down = all(udts_results[tf]["direction"] == "DOWN" for tf in ["monthly", "weekly", "daily"])
        
        support_prices = {}
        support_distances = {}
        
        for tf in timeframes:
            direction = udts_results[tf]["direction"]
            support = get_support_price(ohlc_data[tf], direction)
            support_prices[tf] = support
            
            if support and cmp and cmp > 0:
                distance_pct = round((support - cmp) / cmp * 100, 2)
                support_distances[tf] = distance_pct
            else:
                support_distances[tf] = None
        
        base_score = sum(100 if udts_results[tf]["direction"] == "UP" else -100 for tf in timeframes)
        daily_support = support_prices.get("daily")
        
        cmp_label = "NO"
        cmp_direction = None
        cmp_score = 0
        
        if cmp and daily_support:
            if is_triple_up:
                if cmp > daily_support:
                    cmp_label = "YES"
                    cmp_direction = "UP"
                    cmp_score = 100
                else:
                    cmp_label = "NO"
                    cmp_direction = "DOWN"
                    cmp_score = 0
            elif is_triple_down:
                if cmp < daily_support:
                    cmp_label = "YES"
                    cmp_direction = "DOWN"
                    cmp_score = -100
                else:
                    cmp_label = "NO"
                    cmp_direction = "UP"
                    cmp_score = 0
        
        # Get ALL candles from today's trading session (or last session if market closed)
        all_15min_candles = get_ohlc_data(symbol, "15min")
        todays_session_candles = get_todays_session_candles(all_15min_candles)
        
        # Remove the last candle ONLY if market is currently open (it's incomplete/forming)
        # If market is closed, all candles from last session are complete
        market_open = is_market_currently_open()
        if market_open:
            closed_session_candles = todays_session_candles[:-1] if len(todays_session_candles) > 1 else todays_session_candles
        else:
            # Market closed - all session candles are complete, use them all
            closed_session_candles = todays_session_candles
        
        # Calculate blocks for biggest trend using ALL session candles
        blocks_15min = calculate_15min_blocks(closed_session_candles) if closed_session_candles else []
        biggest_trend = get_biggest_trend(blocks_15min)
        
        candle_9_15_to_9_30 = get_9_15_to_9_30_candle(all_15min_candles)
        
        initial_trend = None
        initial_score = 0
        
        if candle_9_15_to_9_30:
            candle_is_green = is_green(candle_9_15_to_9_30)
            candle_is_red = is_red(candle_9_15_to_9_30)
            
            if candle_is_green:
                initial_trend = {
                    "direction": "UP",
                    "support": candle_9_15_to_9_30["open"]
                }
                if is_triple_up:
                    initial_score = 100
            elif candle_is_red:
                initial_trend = {
                    "direction": "DOWN",
                    "support": candle_9_15_to_9_30["open"]
                }
                if is_triple_down:
                    initial_score = -100
        
        biggest_score = 0
        if biggest_trend:
            if is_triple_up and biggest_trend["direction"] == "UP":
                biggest_score = 100
            elif is_triple_down and biggest_trend["direction"] == "DOWN":
                biggest_score = -100
        
        total_score = base_score + cmp_score + biggest_score + initial_score
        
        target = fundamentals.get("target_price")
        upside = None
        if target and cmp and cmp > 0:
            upside = round((target - cmp) / cmp * 100, 1)
        
        dist1_signed = None
        dist2_signed = None
        
        if cmp and cmp > 0 and biggest_trend and biggest_trend["start_price"]:
            dist1_signed = round((biggest_trend["start_price"] - cmp) / cmp * 100, 2)
        if cmp and cmp > 0 and daily_support:
            dist2_signed = round((daily_support - cmp) / cmp * 100, 2)
        
        max_distance = None
        daily_direction = udts_results.get("daily", {}).get("direction")
        
        if daily_direction:
            valid_distances = []
            
            if daily_direction == "UP":
                if dist1_signed is not None and dist1_signed < 0:
                    valid_distances.append(dist1_signed)
                if dist2_signed is not None and dist2_signed < 0:
                    valid_distances.append(dist2_signed)
                
                if valid_distances:
                    max_distance = min(valid_distances)
                    
            elif daily_direction == "DOWN":
                if dist1_signed is not None and dist1_signed > 0:
                    valid_distances.append(dist1_signed)
                if dist2_signed is not None and dist2_signed > 0:
                    valid_distances.append(dist2_signed)
                
                if valid_distances:
                    max_distance = max(valid_distances)
        
        cmp_minus_btf1 = None
        if cmp and biggest_trend and biggest_trend["start_price"]:
            cmp_minus_btf1 = round(cmp - biggest_trend["start_price"], 2)
        
        # Calculate technical indicators using LATEST candle (whether forming or closed)
        # Daily indicators
        daily_rsi = calculate_rsi(all_daily_candles, period=14)
        daily_adx = calculate_adx(all_daily_candles, period=14)
        daily_supertrend = calculate_supertrend(all_daily_candles, atr_period=10, multiplier=3.0)
        daily_bb_pct = calculate_bollinger_bands_pct(all_daily_candles, period=20, std_dev=2.0)
        
        # Weekly indicators
        all_weekly_candles = get_ohlc_data(symbol, "weekly")
        weekly_bb_pct = calculate_bollinger_bands_pct(all_weekly_candles, period=20, std_dev=2.0)
        
        # Monthly indicators
        all_monthly_candles = get_ohlc_data(symbol, "monthly")
        monthly_bb_pct = calculate_bollinger_bands_pct(all_monthly_candles, period=20, std_dev=2.0)
        
        result.update({
            "udts": {tf: udts_results[tf]["direction"] for tf in timeframes},
            "supports": support_prices,
            "support_distances": support_distances,
            "is_triple_up": is_triple_up,
            "is_triple_down": is_triple_down,
            "cmp": cmp,
            "cmp_label": cmp_label,
            "cmp_direction": cmp_direction,
            "cmp_change_pct": cmp_change_pct,
            "yesterday_close": previous_close,
            "daily_support": daily_support,
            "daily_support_pct": dist2_signed,
            "biggest_trend": {
                "direction": biggest_trend["direction"] if biggest_trend else None,
                "support": biggest_trend["start_price"] if biggest_trend else None,
                "distance_pct": dist1_signed,
                "cmp_diff": cmp_minus_btf1,
                "low": biggest_trend["low"] if biggest_trend else None,
                "high": biggest_trend["high"] if biggest_trend else None,
                "start_candle": biggest_trend.get("start_candle") if biggest_trend else None,
                "end_candle": biggest_trend.get("end_candle") if biggest_trend else None
            } if biggest_trend else None,
            "initial_trend": {
                "direction": initial_trend["direction"] if initial_trend else None,
                "support": initial_trend["support"] if initial_trend else None
            } if initial_trend else None,
            "max_distance": max_distance,
            "scores": {
                "base": base_score,
                "cmp": cmp_score,
                "biggest": biggest_score,
                "initial": initial_score,
                "total": total_score
            },
            "fundamentals": fundamentals,
            "upside": upside,
            "two_yr_high_pct": two_yr_high_pct,
            "target_price": target,
            "analyst_count": analyst_count,
            "market_cap_tkc": fundamentals.get("market_cap_tkc"),
            "sector": fundamentals.get("sector"),
            "industry": fundamentals.get("industry"),
            "inst_holding_pct": fundamentals.get("inst_holding_pct"),
            # Technical indicators
            "daily_rsi": daily_rsi,
            "daily_adx": daily_adx,
            "daily_supertrend": daily_supertrend,
            "daily_bb_pct": daily_bb_pct,
            "weekly_bb_pct": weekly_bb_pct,
            "monthly_bb_pct": monthly_bb_pct
        })
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        result["error"] = str(e)
    
    return result

def calculate_nifty50_ad():
    """Calculate Advance/Decline for NIFTY 50 stocks"""
    advances = 0
    declines = 0
    
    nifty50_symbols = get_nifty50_symbols()
    
    now = get_ist_now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    market_open = False
    if weekday in [0, 1, 2, 3, 4]:
        if (hour > 9 or (hour == 9 and minute >= 15)) and (hour < 15 or (hour == 15 and minute < 30)):
            market_open = True
    
    logger.info(f"Calculating A/D - Market {'OPEN' if market_open else 'CLOSED'}")
    
    for symbol in nifty50_symbols:
        try:
            yf_symbol = get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            if market_open:
                intraday = ticker.history(period="1d", interval="5m")
                daily = ticker.history(period="5d", interval="1d")
                
                if not intraday.empty and len(daily) >= 2:
                    curr_price = float(intraday["Close"].iloc[-1])
                    prev_close = float(daily["Close"].iloc[-2])
                    
                    if curr_price > prev_close:
                        advances += 1
                    elif curr_price < prev_close:
                        declines += 1
                elif len(daily) >= 2:
                    curr_close = float(daily["Close"].iloc[-1])
                    prev_close = float(daily["Close"].iloc[-2])
                    if curr_close > prev_close:
                        advances += 1
                    elif curr_close < prev_close:
                        declines += 1
            else:
                daily = ticker.history(period="5d", interval="1d")
                
                if len(daily) >= 2:
                    curr_close = float(daily["Close"].iloc[-1])
                    prev_close = float(daily["Close"].iloc[-2])
                    
                    if curr_close > prev_close:
                        advances += 1
                    elif curr_close < prev_close:
                        declines += 1
                    
        except Exception as e:
            logger.warning(f"Error getting A/D for {symbol}: {e}")
            continue
    
    logger.info(f"A/D Results: {advances} advances, {declines} declines")
    return advances, declines

def get_nifty50_data() -> Dict:
    """Get NIFTY 50 index data with fallback to last available data"""
    # Check in-memory cache first (15 min validity)
    with cache_lock:
        if cache["nifty50"]["data"] and is_cache_valid(cache["nifty50"]["timestamp"], 15):
            return cache["nifty50"]["data"]
    
    try:
        nifty = yf.Ticker("^NSEI")
        
        # Get daily data first (for prices and pivot)
        daily = nifty.history(period="5d", interval="1d")
        
        # If no daily data available, try to get from Supabase (last available session)
        if daily.empty:
            logger.warning("No fresh NIFTY50 data available, trying Supabase cache")
            cached = get_stock_list('nifty50_index', None)
            if cached:
                logger.info("Using last available NIFTY50 data from Supabase")
                return cached
            logger.warning("No cached NIFTY50 data found")
            return {}
        
        # Get 15-min data (still needed for blocks calculation)
        hist = nifty.history(period="5d", interval="15m")
        
        # Current price = last DAILY close
        current = float(daily["Close"].iloc[-1])
        
        # Previous close = second-last DAILY close
        prev_close = float(daily["Close"].iloc[-2]) if len(daily) > 1 else current
        change_pct = round((current - prev_close) / prev_close * 100, 2)
        
        # Pivot calculation using last DAILY candle
        last_daily = daily.iloc[-1]
        pivot = round((float(last_daily["High"]) + float(last_daily["Low"]) + float(last_daily["Close"])) / 3, 2)
        
        candles = []
        for idx, row in hist.iterrows():
            candles.append({
                "timestamp": idx.isoformat(),
                "open": float(row["Open"]),
                "close": float(row["Close"]),
                "high": float(row["High"]),
                "low": float(row["Low"])
            })
        
        # Remove last candle ONLY if market is currently open
        market_open = is_market_currently_open()
        if market_open:
            closed_candles = candles[:-1] if len(candles) > 1 else candles
        else:
            # Market closed - all candles are complete
            closed_candles = candles
        
        blocks = calculate_15min_blocks(closed_candles[-24:]) if closed_candles else []
        biggest = get_biggest_trend(blocks)
        
        advances, declines = calculate_nifty50_ad()
        
        result = {
            "value": round(current, 2),
            "change_pct": change_pct,
            "pivot": pivot,
            "above_pivot": current >= pivot,
            "biggest_trend": biggest["direction"] if biggest else None,
            "biggest_trend_support": round(biggest["start_price"], 2) if biggest else None,
            "advance": advances,
            "decline": declines
        }
        
        # Save to both in-memory cache and Supabase for fallback
        with cache_lock:
            cache["nifty50"] = {"data": result, "timestamp": get_ist_now()}

        # Save to Supabase as last valid data (no expiry for fallback)
        save_stock_list('nifty50_index', result)

        return result
    except Exception as e:
        logger.error(f"Error fetching NIFTY 50: {e}")
        # Try Supabase fallback on error
        cached = get_stock_list('nifty50_index', None)
        if cached:
            logger.info("Using last available NIFTY50 data from Supabase (after error)")
            return cached
        return {}

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "UDTS Stock Analyzer API"}

@api_router.get("/health")
async def api_health():
    """Health check endpoint for API router"""
    return {"status": "healthy", "service": "UDTS Stock Analyzer API", "database": "supabase", "db_status": "connected" if SUPABASE_AVAILABLE else "unavailable", "timestamp": get_ist_now().isoformat()}

@api_router.get("/nifty50")
async def get_nifty50():
    return get_nifty50_data()

@api_router.get("/symbols")
async def get_symbols(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return {"symbols": get_nifty500_symbols()}

@api_router.get("/stock/{symbol}")
async def get_stock(symbol: str):
    return analyze_stock(symbol.upper())

@api_router.get("/stocks")
async def get_all_stocks(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    symbols = get_nifty500_symbols()
    results = []
    
    logger.info(f"Starting BATCH PARALLEL analysis of {len(symbols)} stocks (20 stocks per batch)")
    logger.info("Estimated time: 4-6 minutes with Supabase cache, ensuring NO UNKNOWN values")
    
    # Process stocks in BATCHES of 20 with parallel processing
    # Optimized batch size balances speed with rate limit avoidance and ensures complete data
    batch_size = 20
    total_batches = (len(symbols) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(symbols), batch_size):
        batch_symbols = symbols[batch_idx:batch_idx + batch_size]
        batch_num = (batch_idx // batch_size) + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_symbols)} stocks)")
        
        # Process batch in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_symbol = {executor.submit(analyze_stock, symbol): symbol for symbol in batch_symbols}
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results.append({"symbol": symbol, "error": str(e)})
        
        # Progress logging
        processed = min(batch_idx + batch_size, len(symbols))
        logger.info(f"Progress: {processed}/{len(symbols)} stocks analyzed ({(processed / len(symbols) * 100):.1f}%)")
        
        # Small delay between batches to avoid overwhelming the API
        # 0.8 second per batch = ~20 seconds total for 500 stocks in ~25 batches (batch size 20)
        if batch_idx + batch_size < len(symbols):
            time.sleep(0.8)
    
    logger.info(f"Completed batch parallel analysis of {len(results)} stocks")
    
    def sort_key(x):
        score = x.get("scores", {}).get("total", -999)
        upside = x.get("upside") if x.get("upside") is not None else -999
        return (-score, -upside)
    
    results.sort(key=sort_key)
    
    return {
        "stocks": results,
        "timestamp": get_ist_now().isoformat()
    }

@api_router.get("/sector-trends")
async def get_sector_trends(response: Response):
    """Calculate sector trends based on Triple UDTS Score (Monthly + Weekly + Daily)"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    try:
        symbols = get_nifty500_symbols()
        
        # Collect all stock data with sectors
        sector_stocks = {}  # {sector: [stock_data, ...]}
        
        logger.info(f"Calculating sector trends for {len(symbols)} stocks (BATCH PARALLEL)")
        
        # Process stocks in BATCHES of 20 with parallel processing
        batch_size = 20
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(symbols), batch_size):
            batch_symbols = symbols[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_symbol = {executor.submit(analyze_stock, symbol): symbol for symbol in batch_symbols}
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        stock_data = future.result()
                        
                        # Only process stocks with valid sector and UDTS data
                        sector = stock_data.get("sector")
                        if sector and stock_data.get("udts"):
                            udts = stock_data["udts"]
                            
                            # Calculate Triple UDTS Score (Monthly + Weekly + Daily only)
                            monthly = udts.get("monthly")
                            weekly = udts.get("weekly")
                            daily = udts.get("daily")
                            
                            monthly_score = 100 if monthly == "UP" else -100 if monthly == "DOWN" else 0
                            weekly_score = 100 if weekly == "UP" else -100 if weekly == "DOWN" else 0
                            daily_score = 100 if daily == "UP" else -100 if daily == "DOWN" else 0
                            
                            triple_score = monthly_score + weekly_score + daily_score
                            
                            # Check if stock is fully UP or fully DOWN (all three timeframes)
                            is_fully_up = (monthly == "UP" and weekly == "UP" and daily == "UP")
                            is_fully_down = (monthly == "DOWN" and weekly == "DOWN" and daily == "DOWN")
                            
                            if sector not in sector_stocks:
                                sector_stocks[sector] = []
                            
                            # Get fundamental data for the stock
                            fundamentals = stock_data.get("fundamentals", {})
                            
                            sector_stocks[sector].append({
                                "symbol": stock_data["symbol"],
                                "triple_score": triple_score,
                                "is_fully_up": is_fully_up,
                                "is_fully_down": is_fully_down,
                                "dividend_yield": fundamentals.get("dividend_yield"),
                                "enterprise_to_ebitda": fundamentals.get("enterprise_to_ebitda"),
                                "enterprise_to_revenue": fundamentals.get("enterprise_to_revenue")
                            })
                    except Exception as e:
                        logger.error(f"Error processing {symbol} for sector trends: {e}")
            
            # Progress logging
            if (batch_idx // batch_size + 1) % 20 == 0:
                processed = min(batch_idx + batch_size, len(symbols))
                logger.info(f"Sector trends progress: {processed}/{len(symbols)} stocks")
            
            # Small delay between batches
            if batch_idx + batch_size < len(symbols):
                time.sleep(1)
        
        # Calculate median score and percentage metrics for each sector
        sector_trends = []
        for sector, stocks in sector_stocks.items():
            if len(stocks) > 0:
                scores = [s["triple_score"] for s in stocks]
                # Calculate median
                scores_sorted = sorted(scores)
                n = len(scores_sorted)
                if n % 2 == 0:
                    median_score = (scores_sorted[n//2 - 1] + scores_sorted[n//2]) / 2
                else:
                    median_score = scores_sorted[n//2]
                
                # Calculate % of stocks fully UP and fully DOWN
                fully_up_count = sum(1 for s in stocks if s["is_fully_up"])
                fully_down_count = sum(1 for s in stocks if s["is_fully_down"])
                pct_fully_up = (fully_up_count / len(stocks)) * 100
                pct_fully_down = (fully_down_count / len(stocks)) * 100
                
                sector_trends.append({
                    "sector": sector,
                    "median_score": round(median_score, 2),
                    "stock_count": len(stocks),
                    "fully_up_count": fully_up_count,
                    "pct_fully_up": round(pct_fully_up, 2),
                    "fully_down_count": fully_down_count,
                    "pct_fully_down": round(pct_fully_down, 2),
                    "stocks": stocks  # Include stocks for details
                })
        
        # Sort and get top 5 UP trends (primary: median score desc, secondary: % fully UP desc)
        up_trends = sorted(
            [s for s in sector_trends if s["median_score"] > 0],
            key=lambda x: (x["median_score"], x["pct_fully_up"]),
            reverse=True
        )[:5]
        
        # Sort and get top 5 DOWN trends (primary: median score asc, secondary: % fully DOWN desc)
        down_trends = sorted(
            [s for s in sector_trends if s["median_score"] < 0],
            key=lambda x: (x["median_score"], -x["pct_fully_down"])
        )[:5]
        
        logger.info(f"Sector trends calculated: {len(up_trends)} UP, {len(down_trends)} DOWN")
        
        return {
            "up_trends": up_trends,
            "down_trends": down_trends,
            "timestamp": get_ist_now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating sector trends: {e}")
        return {
            "up_trends": [],
            "down_trends": [],
            "error": str(e),
            "timestamp": get_ist_now().isoformat()
        }

@api_router.get("/industry-trends")
async def get_industry_trends(response: Response):
    """Calculate industry trends based on Triple UDTS Score (Monthly + Weekly + Daily)"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    try:
        symbols = get_nifty500_symbols()
        
        # Collect all stock data with industries
        industry_stocks = {}  # {industry: [stock_data, ...]}
        
        logger.info(f"Calculating industry trends for {len(symbols)} stocks (BATCH PARALLEL)")
        
        # Process stocks in BATCHES of 20 with parallel processing
        batch_size = 20
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(symbols), batch_size):
            batch_symbols = symbols[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_symbol = {executor.submit(analyze_stock, symbol): symbol for symbol in batch_symbols}
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        stock_data = future.result()
                        
                        # Only process stocks with valid industry and UDTS data
                        industry = stock_data.get("industry")
                        if industry and stock_data.get("udts"):
                            udts = stock_data["udts"]
                            
                            # Calculate Triple UDTS Score (Monthly + Weekly + Daily only)
                            monthly = udts.get("monthly")
                            weekly = udts.get("weekly")
                            daily = udts.get("daily")
                            
                            monthly_score = 100 if monthly == "UP" else -100 if monthly == "DOWN" else 0
                            weekly_score = 100 if weekly == "UP" else -100 if weekly == "DOWN" else 0
                            daily_score = 100 if daily == "UP" else -100 if daily == "DOWN" else 0
                            
                            triple_score = monthly_score + weekly_score + daily_score
                            
                            # Check if stock is fully UP or fully DOWN (all three timeframes)
                            is_fully_up = (monthly == "UP" and weekly == "UP" and daily == "UP")
                            is_fully_down = (monthly == "DOWN" and weekly == "DOWN" and daily == "DOWN")
                            
                            if industry not in industry_stocks:
                                industry_stocks[industry] = []
                            
                            # Get fundamental data for the stock
                            fundamentals = stock_data.get("fundamentals", {})
                            
                            industry_stocks[industry].append({
                                "symbol": stock_data["symbol"],
                                "triple_score": triple_score,
                                "is_fully_up": is_fully_up,
                                "is_fully_down": is_fully_down,
                                "dividend_yield": fundamentals.get("dividend_yield"),
                                "enterprise_to_ebitda": fundamentals.get("enterprise_to_ebitda"),
                                "enterprise_to_revenue": fundamentals.get("enterprise_to_revenue")
                            })
                    except Exception as e:
                        logger.error(f"Error processing {symbol} for industry trends: {e}")
            
            # Progress logging
            if (batch_idx // batch_size + 1) % 20 == 0:
                processed = min(batch_idx + batch_size, len(symbols))
                logger.info(f"Industry trends progress: {processed}/{len(symbols)} stocks")
            
            # Small delay between batches
            if batch_idx + batch_size < len(symbols):
                time.sleep(1)
        
        # Calculate median score and percentage metrics for each industry
        industry_trends = []
        for industry, stocks in industry_stocks.items():
            if len(stocks) > 0:
                scores = [s["triple_score"] for s in stocks]
                # Calculate median
                scores_sorted = sorted(scores)
                n = len(scores_sorted)
                if n % 2 == 0:
                    median_score = (scores_sorted[n//2 - 1] + scores_sorted[n//2]) / 2
                else:
                    median_score = scores_sorted[n//2]
                
                # Calculate % of stocks fully UP and fully DOWN
                fully_up_count = sum(1 for s in stocks if s["is_fully_up"])
                fully_down_count = sum(1 for s in stocks if s["is_fully_down"])
                pct_fully_up = (fully_up_count / len(stocks)) * 100
                pct_fully_down = (fully_down_count / len(stocks)) * 100
                
                industry_trends.append({
                    "industry": industry,
                    "median_score": round(median_score, 2),
                    "stock_count": len(stocks),
                    "fully_up_count": fully_up_count,
                    "pct_fully_up": round(pct_fully_up, 2),
                    "fully_down_count": fully_down_count,
                    "pct_fully_down": round(pct_fully_down, 2),
                    "stocks": stocks  # Include stocks for details
                })
        
        # Sort and get top 10 UP trends (primary: median score desc, secondary: % fully UP desc)
        up_trends = sorted(
            [s for s in industry_trends if s["median_score"] > 0],
            key=lambda x: (x["median_score"], x["pct_fully_up"]),
            reverse=True
        )[:10]
        
        # Sort and get top 10 DOWN trends (primary: median score asc, secondary: % fully DOWN desc)
        down_trends = sorted(
            [s for s in industry_trends if s["median_score"] < 0],
            key=lambda x: (x["median_score"], -x["pct_fully_down"])
        )[:10]
        
        logger.info(f"Industry trends calculated: {len(up_trends)} UP, {len(down_trends)} DOWN")
        
        return {
            "up_trends": up_trends,
            "down_trends": down_trends,
            "timestamp": get_ist_now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating industry trends: {e}")
        return {
            "up_trends": [],
            "down_trends": [],
            "error": str(e),
            "timestamp": get_ist_now().isoformat()
        }

@api_router.get("/refresh")
async def refresh_data():
    global cache
    
    # Clear in-memory cache
    with cache_lock:
        cache["ohlc"] = {}
        cache["fundamentals"] = {}
        cache["institutional_holdings"] = {}
        cache["nifty50"] = {"data": None, "timestamp": None}
        cache["nifty50_list"] = {"data": None, "timestamp": None}
        cache["nifty500_list"] = {"data": None, "timestamp": None}

    # Clear Supabase cache
    if clear_all_caches():
        logger.info("Supabase caches cleared (OHLC, fundamentals, and institutional holdings)")
    else:
        logger.warning("Error clearing Supabase caches or Supabase not available")

    logger.info("All caches cleared - will fetch fresh data on next request")
    return {"message": "Cache cleared", "timestamp": get_ist_now().isoformat()}

@api_router.get("/refresh_stock_list")
async def refresh_stock_list():
    """Manually refresh NIFTY 500 stock list from NSE CSV"""
    global cache
    
    try:
        # Store old list for comparison
        old_list = None
        with cache_lock:
            if cache["nifty500_list"]["data"]:
                old_list = cache["nifty500_list"]["data"].copy()
        
        import time
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.niftyindices.com/',
        })
        
        logger.info("Manually refreshing NIFTY 500 list - Step 1: Getting cookies")
        
        time.sleep(1)
        main_response = session.get('https://www.niftyindices.com/', timeout=20)
        
        if main_response.status_code != 200:
            logger.warning(f"Failed to load main page: HTTP {main_response.status_code}")
            return {
                "success": False,
                "message": f"Failed to access NSE website. Using cached/fallback list.",
                "timestamp": get_ist_now().isoformat()
            }
        
        time.sleep(2)
        
        logger.info("Step 2: Fetching NIFTY 500 CSV from NSE")
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
        
        response = session.get(url, timeout=60)
        
        if response.status_code == 200:
            if 'DOCTYPE' in response.text[:500] or '<html' in response.text[:500].lower():
                logger.warning("Received HTML instead of CSV")
                return {
                    "success": False,
                    "message": "Failed to fetch CSV from NSE. Using cached/fallback list.",
                    "timestamp": get_ist_now().isoformat()
                }
            
            csv_content = StringIO(response.text)
            csv_reader = csv.DictReader(csv_content)
            
            symbols = []
            for row in csv_reader:
                symbol = row.get('Symbol', '').strip()
                if is_valid_symbol(symbol):
                    symbols.append(symbol)
            
            logger.info(f"Fetched {len(symbols)} valid stocks from NSE CSV")
            
            if len(symbols) < 50:
                logger.warning(f"Only {len(symbols)} stocks found")
                return {
                    "success": False,
                    "message": f"Invalid data from NSE (only {len(symbols)} stocks). Using cached/fallback list.",
                    "timestamp": get_ist_now().isoformat()
                }
            
            symbols = symbols[:500]
            
            list_changed = False
            if old_list is None or set(symbols) != set(old_list) or len(symbols) != len(old_list):
                list_changed = True
                logger.info("Stock list HAS CHANGED - clearing all caches")
                
                with cache_lock:
                    cache["ohlc"] = {}
                    cache["fundamentals"] = {}
                    cache["nifty50"] = {"data": None, "timestamp": None}
                    cache["nifty50_list"] = {"data": None, "timestamp": None}
                    cache["nifty500_list"] = {"data": symbols, "timestamp": get_ist_now()}
                
                save_stock_list('nifty500', symbols)

                if clear_all_caches():
                    logger.info("Supabase caches cleared due to list change")
                else:
                    logger.warning("Error clearing Supabase caches")
            else:
                logger.info("Stock list unchanged - keeping existing caches")
                with cache_lock:
                    cache["nifty500_list"] = {"data": symbols, "timestamp": get_ist_now()}
                save_stock_list('nifty500', symbols)
            
            return {
                "success": True,
                "message": "Stock list refreshed from NSE",
                "list_changed": list_changed,
                "stock_count": len(symbols),
                "cache_cleared": list_changed,
                "timestamp": get_ist_now().isoformat()
            }
        else:
            logger.warning(f"Failed to fetch from NSE: HTTP {response.status_code}")
            return {
                "success": False,
                "message": f"Failed to fetch from NSE (HTTP {response.status_code}). Using cached/fallback list.",
                "timestamp": get_ist_now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error refreshing stock list: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}. Using cached/fallback list.",
            "timestamp": get_ist_now().isoformat()
        }

app.include_router(api_router)

# Add GZip compression middleware for faster data transfer
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

@app.get("/")
async def root_health():
    return {"status": "healthy", "service": "UDTS Stock Analyzer API", "database": "supabase", "db_status": "connected" if SUPABASE_AVAILABLE else "unavailable"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "supabase", "db_status": "connected" if SUPABASE_AVAILABLE else "unavailable"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down server")
