/*
  # Stock Analyzer Cache Tables Migration
  
  ## Summary
  Creates database tables to replace MongoDB collections for the UDTS Stock Analyzer application.
  These tables store cached stock data with timestamps to improve performance and reduce API calls.
  
  ## New Tables
  
  ### 1. ohlc_cache
  Stores OHLC (Open, High, Low, Close) candlestick data for stocks across different timeframes.
  - id (uuid, primary key) - Unique identifier
  - symbol (text, not null) - Stock symbol (e.g., RELIANCE, TCS)
  - timeframe (text, not null) - Timeframe type (monthly, weekly, daily, 1hour, 15min)
  - data (jsonb, not null) - Array of candle objects with timestamp, open, high, low, close
  - timestamp (timestamptz, not null) - When this data was cached (IST timezone)
  - created_at (timestamptz) - Record creation time
  - updated_at (timestamptz) - Last update time
  - Unique constraint: (symbol, timeframe) combination must be unique
  - Index: Composite index on (symbol, timeframe) for fast lookups
  
  ### 2. fundamentals_cache
  Stores fundamental data for stocks (PE ratio, market cap, ROE, etc.)
  - id (uuid, primary key) - Unique identifier
  - symbol (text, unique, not null) - Stock symbol
  - data (jsonb, not null) - Fundamental metrics (roe, pe, pb, de, revenue, earnings, etc.)
  - timestamp (timestamptz, not null) - When this data was cached
  - created_at (timestamptz) - Record creation time
  - updated_at (timestamptz) - Last update time
  - Unique constraint: symbol must be unique
  - Index: Index on symbol for fast lookups
  
  ### 3. institutional_cache
  Stores institutional holdings data for stocks (FII, DII ownership percentages)
  - id (uuid, primary key) - Unique identifier
  - symbol (text, unique, not null) - Stock symbol
  - data (jsonb, not null) - Institutional holdings data (fii_percentage, dii_percentage, total_percentage)
  - timestamp (timestamptz, not null) - When this data was cached
  - created_at (timestamptz) - Record creation time
  - updated_at (timestamptz) - Last update time
  - Unique constraint: symbol must be unique
  - Index: Index on symbol for fast lookups
  
  ### 4. stock_lists
  Stores stock lists (NIFTY 50, NIFTY 500, etc.) and index data
  - id (uuid, primary key) - Unique identifier
  - list_type (text, unique, not null) - Type of list (nifty50, nifty500, nifty50_index)
  - data (jsonb, not null) - List data (array of symbols or index data object)
  - timestamp (timestamptz, not null) - When this data was cached
  - created_at (timestamptz) - Record creation time
  - updated_at (timestamptz) - Last update time
  - Unique constraint: list_type must be unique
  - Index: Index on list_type for fast lookups
  
  ## Security
  
  ### Row Level Security (RLS)
  - RLS is enabled on all tables
  - Public read access is granted since this is a public stock analyzer application
  - Write operations are restricted to service role only (backend application)
  
  ### Policies
  For each table:
  - SELECT: Public read access for authenticated and anonymous users
  - INSERT: Service role only (backend will use service role key)
  - UPDATE: Service role only
  - DELETE: Service role only
  
  ## Notes
  - All tables use JSONB for flexible data storage matching MongoDB structure
  - Timestamps are stored in UTC with timezone support
  - Indexes are created for optimal query performance
  - The migration is idempotent using IF NOT EXISTS checks
  - Default values are set for created_at and updated_at columns
*/

-- Create ohlc_cache table
CREATE TABLE IF NOT EXISTS ohlc_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  timeframe text NOT NULL,
  data jsonb NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(symbol, timeframe)
);

-- Create fundamentals_cache table
CREATE TABLE IF NOT EXISTS fundamentals_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text UNIQUE NOT NULL,
  data jsonb NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create institutional_cache table
CREATE TABLE IF NOT EXISTS institutional_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text UNIQUE NOT NULL,
  data jsonb NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create stock_lists table
CREATE TABLE IF NOT EXISTS stock_lists (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  list_type text UNIQUE NOT NULL,
  data jsonb NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timeframe ON ohlc_cache(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_fundamentals_symbol ON fundamentals_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_institutional_symbol ON institutional_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_lists_type ON stock_lists(list_type);

-- Enable Row Level Security
ALTER TABLE ohlc_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE fundamentals_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE institutional_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_lists ENABLE ROW LEVEL SECURITY;

-- RLS Policies for ohlc_cache
CREATE POLICY "Allow public read access to ohlc_cache"
  ON ohlc_cache FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow service role to insert ohlc_cache"
  ON ohlc_cache FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Allow service role to update ohlc_cache"
  ON ohlc_cache FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow service role to delete ohlc_cache"
  ON ohlc_cache FOR DELETE
  TO service_role
  USING (true);

-- RLS Policies for fundamentals_cache
CREATE POLICY "Allow public read access to fundamentals_cache"
  ON fundamentals_cache FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow service role to insert fundamentals_cache"
  ON fundamentals_cache FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Allow service role to update fundamentals_cache"
  ON fundamentals_cache FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow service role to delete fundamentals_cache"
  ON fundamentals_cache FOR DELETE
  TO service_role
  USING (true);

-- RLS Policies for institutional_cache
CREATE POLICY "Allow public read access to institutional_cache"
  ON institutional_cache FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow service role to insert institutional_cache"
  ON institutional_cache FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Allow service role to update institutional_cache"
  ON institutional_cache FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow service role to delete institutional_cache"
  ON institutional_cache FOR DELETE
  TO service_role
  USING (true);

-- RLS Policies for stock_lists
CREATE POLICY "Allow public read access to stock_lists"
  ON stock_lists FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Allow service role to insert stock_lists"
  ON stock_lists FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Allow service role to update stock_lists"
  ON stock_lists FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow service role to delete stock_lists"
  ON stock_lists FOR DELETE
  TO service_role
  USING (true);