"""Test script to verify TMPV UDTS bug on monthly timeframe"""
import yfinance as yf
from datetime import datetime

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_udts_current(candles):
    """Current UDTS logic (with bug)"""
    if not candles:
        return {"direction": "UNKNOWN", "g1": None, "r1": None, "r2": None, "g2": None}
    
    g1_idx = None
    r1_idx = None
    
    # Find G1 and R1
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
        last_closed = candles[-1]
        direction = "UP" if is_green(last_closed) else "DOWN"
        return {"direction": direction, "g1": None, "r1": None, "r2": None, "g2": None}
    
    r2_idx = None
    g2_idx = None
    
    # Find R2 and G2 - BUGGY LOGIC
    for i in range(g1_idx + 1, len(candles)):
        if is_red(candles[i]):
            for j in range(i - 1, -1, -1):  # BUG: Goes all the way back to 0
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
        "g2": candles[g2_idx] if g2_idx is not None else None,
        "g1_idx": g1_idx,
        "r1_idx": r1_idx,
        "r2_idx": r2_idx,
        "g2_idx": g2_idx
    }

def calculate_udts_fixed(candles):
    """Fixed UDTS logic"""
    if not candles:
        return {"direction": "UNKNOWN", "g1": None, "r1": None, "r2": None, "g2": None}
    
    g1_idx = None
    r1_idx = None
    
    # Find G1 and R1
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
        last_closed = candles[-1]
        direction = "UP" if is_green(last_closed) else "DOWN"
        return {"direction": direction, "g1": None, "r1": None, "r2": None, "g2": None}
    
    r2_idx = None
    g2_idx = None
    
    # Find R2 and G2 - FIXED LOGIC
    for i in range(g1_idx + 1, len(candles)):
        if is_red(candles[i]):
            for j in range(i - 1, g1_idx, -1):  # FIX: Only look at candles AFTER G1
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
        "g2": candles[g2_idx] if g2_idx is not None else None,
        "g1_idx": g1_idx,
        "r1_idx": r1_idx,
        "r2_idx": r2_idx,
        "g2_idx": g2_idx
    }

# Fetch TMPV monthly data
print("Fetching TMPV monthly data...")
ticker = yf.Ticker("TMPV.NS")
hist = ticker.history(period="5y", interval="1mo")

if hist.empty:
    print("No data found for TMPV.NS")
    exit()

# Convert to candle format
candles = []
for idx, row in hist.iterrows():
    candles.append({
        "timestamp": idx.strftime("%Y-%m-%d"),
        "open": float(row['Open']),
        "high": float(row['High']),
        "low": float(row['Low']),
        "close": float(row['Close']),
        "volume": int(row['Volume'])
    })

print(f"\nTotal candles: {len(candles)}")
print("\n=== ALL CANDLES ===")
for i, candle in enumerate(candles):
    color = "GREEN" if is_green(candle) else "RED" if is_red(candle) else "DOJI"
    print(f"{i:2d}. {candle['timestamp']}: O={candle['open']:.2f} C={candle['close']:.2f} [{color}]")

# Test with current (buggy) logic
print("\n\n=== TESTING WITH CURRENT (BUGGY) LOGIC ===")
result_current = calculate_udts_current(candles)
print(f"Direction: {result_current['direction']}")
if result_current['g1']:
    print(f"G1 (idx {result_current['g1_idx']}): {result_current['g1']['timestamp']} - O={result_current['g1']['open']:.2f} C={result_current['g1']['close']:.2f}")
if result_current['r1']:
    print(f"R1 (idx {result_current['r1_idx']}): {result_current['r1']['timestamp']} - O={result_current['r1']['open']:.2f} C={result_current['r1']['close']:.2f}")
if result_current['r2']:
    print(f"R2 (idx {result_current['r2_idx']}): {result_current['r2']['timestamp']} - O={result_current['r2']['open']:.2f} C={result_current['r2']['close']:.2f}")
if result_current['g2']:
    print(f"G2 (idx {result_current['g2_idx']}): {result_current['g2']['timestamp']} - O={result_current['g2']['open']:.2f} C={result_current['g2']['close']:.2f}")

# Test with fixed logic
print("\n\n=== TESTING WITH FIXED LOGIC ===")
result_fixed = calculate_udts_fixed(candles)
print(f"Direction: {result_fixed['direction']}")
if result_fixed['g1']:
    print(f"G1 (idx {result_fixed['g1_idx']}): {result_fixed['g1']['timestamp']} - O={result_fixed['g1']['open']:.2f} C={result_fixed['g1']['close']:.2f}")
if result_fixed['r1']:
    print(f"R1 (idx {result_fixed['r1_idx']}): {result_fixed['r1']['timestamp']} - O={result_fixed['r1']['open']:.2f} C={result_fixed['r1']['close']:.2f}")
if result_fixed['r2']:
    print(f"R2 (idx {result_fixed['r2_idx']}): {result_fixed['r2']['timestamp']} - O={result_fixed['r2']['open']:.2f} C={result_fixed['r2']['close']:.2f}")
if result_fixed['g2']:
    print(f"G2 (idx {result_fixed['g2_idx']}): {result_fixed['g2']['timestamp']} - O={result_fixed['g2']['open']:.2f} C={result_fixed['g2']['close']:.2f}")

print("\n\n=== ANALYSIS ===")
if result_current['direction'] != result_fixed['direction']:
    print(f"⚠️  BUG CONFIRMED! Direction changed from {result_current['direction']} to {result_fixed['direction']}")
    if result_current['g2_idx'] is not None and result_fixed['g1_idx'] is not None:
        if result_current['g2_idx'] <= result_fixed['g1_idx']:
            print(f"🐛 Bug cause: G2 (idx {result_current['g2_idx']}) was found BEFORE or AT G1 (idx {result_fixed['g1_idx']})")
            print(f"   This violates UDTS rules - G2 must come AFTER G1")
else:
    print(f"✓ Both logics agree: Direction is {result_current['direction']}")
