"""
Database module for Supabase operations
Replaces MongoDB with Supabase PostgreSQL
"""

from datetime import datetime, timezone, timedelta
from supabase import create_client, Client
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

# Supabase connection
SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

supabase: Optional[Client] = None
SUPABASE_AVAILABLE = False

def init_supabase():
    """Initialize Supabase client"""
    global supabase, SUPABASE_AVAILABLE

    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase credentials not found in environment")
            return False

        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Test connection by querying stock_lists table
        supabase.table('stock_lists').select('id').limit(1).execute()

        logger.info("Supabase connected successfully")
        SUPABASE_AVAILABLE = True
        return True
    except Exception as e:
        logger.warning(f"Supabase not available: {e}")
        SUPABASE_AVAILABLE = False
        return False

def get_ist_now():
    """Get current time in IST timezone"""
    return datetime.now(IST)

def is_cache_valid(timestamp_str: Optional[str], max_age_minutes: int) -> bool:
    """Check if cached data is still valid based on timestamp"""
    if not timestamp_str:
        return False

    try:
        # Parse ISO format timestamp
        cached_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_seconds = (now - cached_time).total_seconds()
        return age_seconds < max_age_minutes * 60
    except Exception as e:
        logger.warning(f"Error parsing timestamp: {e}")
        return False

def get_from_supabase(table_name: str, filters: Dict[str, str], max_age_minutes: Optional[int] = None) -> Optional[Any]:
    """
    Get cached data from Supabase

    Args:
        table_name: Name of the table
        filters: Dictionary of column:value pairs to filter by
        max_age_minutes: Maximum age of cache in minutes (None for no expiry check)

    Returns:
        The cached data or None if not found/expired
    """
    if not SUPABASE_AVAILABLE or not supabase:
        return None

    try:
        # Build query
        query = supabase.table(table_name).select('*')

        # Apply filters
        for column, value in filters.items():
            query = query.eq(column, value)

        # Execute query
        response = query.limit(1).execute()

        if response.data and len(response.data) > 0:
            row = response.data[0]

            # Check if cache is still valid
            if max_age_minutes is not None:
                if is_cache_valid(row.get('timestamp'), max_age_minutes):
                    return row.get('data')
                else:
                    return None

            return row.get('data')

        return None
    except Exception as e:
        logger.warning(f"Supabase read error from {table_name}: {e}")
        return None

def save_to_supabase(table_name: str, filters: Dict[str, str], data: Any) -> bool:
    """
    Save data to Supabase cache (upsert operation)

    Args:
        table_name: Name of the table
        filters: Dictionary of column:value pairs to identify the row
        data: The data to cache

    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE or not supabase:
        return False

    try:
        # Prepare the record
        record = {
            **filters,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # Try to upsert (insert or update)
        # First, check if record exists
        existing = supabase.table(table_name).select('id').match(filters).execute()

        if existing.data and len(existing.data) > 0:
            # Update existing record
            row_id = existing.data[0]['id']
            supabase.table(table_name).update(record).eq('id', row_id).execute()
        else:
            # Insert new record
            record['created_at'] = datetime.now(timezone.utc).isoformat()
            supabase.table(table_name).insert(record).execute()

        return True
    except Exception as e:
        logger.warning(f"Supabase write error to {table_name}: {e}")
        return False

def delete_from_supabase(table_name: str, filters: Optional[Dict[str, str]] = None) -> bool:
    """
    Delete records from Supabase

    Args:
        table_name: Name of the table
        filters: Dictionary of column:value pairs to filter by (None to delete all)

    Returns:
        True if successful, False otherwise
    """
    if not SUPABASE_AVAILABLE or not supabase:
        return False

    try:
        query = supabase.table(table_name).delete()

        if filters:
            # Apply filters
            for column, value in filters.items():
                query = query.eq(column, value)
        else:
            # Delete all - use a condition that's always true
            # In Supabase, we need to use a filter, so we'll get all IDs first
            all_records = supabase.table(table_name).select('id').execute()
            if all_records.data:
                for record in all_records.data:
                    supabase.table(table_name).delete().eq('id', record['id']).execute()

        return True
    except Exception as e:
        logger.warning(f"Supabase delete error from {table_name}: {e}")
        return False

# Table-specific helper functions for backward compatibility

def get_ohlc_cache(symbol: str, timeframe: str, max_age_minutes: int = 15) -> Optional[List]:
    """Get OHLC data from cache"""
    return get_from_supabase('ohlc_cache', {'symbol': symbol, 'timeframe': timeframe}, max_age_minutes)

def save_ohlc_cache(symbol: str, timeframe: str, data: List) -> bool:
    """Save OHLC data to cache"""
    return save_to_supabase('ohlc_cache', {'symbol': symbol, 'timeframe': timeframe}, data)

def get_fundamentals_cache(symbol: str, max_age_minutes: int = 1440) -> Optional[Dict]:
    """Get fundamentals data from cache"""
    return get_from_supabase('fundamentals_cache', {'symbol': symbol}, max_age_minutes)

def save_fundamentals_cache(symbol: str, data: Dict) -> bool:
    """Save fundamentals data to cache"""
    return save_to_supabase('fundamentals_cache', {'symbol': symbol}, data)

def get_institutional_cache(symbol: str, max_age_minutes: int = 129600) -> Optional[Dict]:
    """Get institutional holdings data from cache"""
    return get_from_supabase('institutional_cache', {'symbol': symbol}, max_age_minutes)

def save_institutional_cache(symbol: str, data: Dict) -> bool:
    """Save institutional holdings data to cache"""
    return save_to_supabase('institutional_cache', {'symbol': symbol}, data)

def get_stock_list(list_type: str, max_age_minutes: Optional[int] = 1440) -> Optional[Any]:
    """Get stock list from cache"""
    return get_from_supabase('stock_lists', {'list_type': list_type}, max_age_minutes)

def save_stock_list(list_type: str, data: Any) -> bool:
    """Save stock list to cache"""
    return save_to_supabase('stock_lists', {'list_type': list_type}, data)

def clear_all_caches() -> bool:
    """Clear all cache tables"""
    if not SUPABASE_AVAILABLE or not supabase:
        return False

    try:
        # Clear each cache table
        tables = ['ohlc_cache', 'fundamentals_cache', 'institutional_cache']

        for table in tables:
            all_records = supabase.table(table).select('id').execute()
            if all_records.data:
                for record in all_records.data:
                    supabase.table(table).delete().eq('id', record['id']).execute()

        logger.info("All Supabase caches cleared")
        return True
    except Exception as e:
        logger.warning(f"Error clearing Supabase caches: {e}")
        return False
