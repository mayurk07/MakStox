"""Debug script to trace DALBHARAT biggest trend calculation"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_udts(candles):
    """Calculate UDTS direction"""
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
        closed_candles = candles[:-1] if len(candles) > 1 else []
        
        if len(closed_candles) == 0:
            forming_candle = candles[-1]
            direction = "UP" if is_green(forming_candle) else "DOWN"
        else:
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

def calculate_15min_blocks(candles):
    """Partition candles into UDTS blocks"""
    if not candles or len(candles) < 2:
        return []
    
    blocks = []
    current_block = [candles[0]]
    current_direction = "UP" if is_green(candles[0]) else "DOWN"
    
    for i in range(1, len(candles)):
        test_block = current_block + [candles[i]]
        test_udts = calculate_udts(test_block)
        
        if test_udts["direction"] != current_direction and len(current_block) > 0:
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
            
            current_block = [candles[i]]
            current_direction = test_udts["direction"]
        else:
            current_block.append(candles[i])
    
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

def get_biggest_trend(blocks):
    """Get block with maximum power (first occurrence from left to right)"""
    if not blocks:
        return None
    
    max_power = max(b["power"] for b in blocks)
    for b in blocks:
        if b["power"] == max_power:
            return b
    return blocks[0]

# DALBHARAT candles for Jan 1, 2026 (Today's session, closed candles only)
# Based on yfinance data, market is open, so last candle (15:15) is still forming
# Closed candles = all except the last one
candles_today = [
    {"time": "09:15", "open": 2132.90, "close": 2147.50, "high": 2147.50, "low": 2132.90},  # GREEN
    {"time": "09:30", "open": 2147.30, "close": 2146.40, "high": 2159.70, "low": 2146.40},  # RED
    {"time": "09:45", "open": 2148.30, "close": 2122.30, "high": 2150.50, "low": 2122.30},  # RED
    {"time": "10:00", "open": 2123.70, "close": 2118.80, "high": 2123.70, "low": 2118.50},  # RED
    {"time": "10:15", "open": 2120.10, "close": 2119.10, "high": 2122.30, "low": 2110.50},  # RED
    {"time": "10:30", "open": 2120.00, "close": 2122.70, "high": 2124.80, "low": 2115.70},  # GREEN
    {"time": "10:45", "open": 2122.60, "close": 2126.60, "high": 2128.30, "low": 2122.30},  # GREEN
    {"time": "11:00", "open": 2126.20, "close": 2142.20, "high": 2144.80, "low": 2126.20},  # GREEN
    {"time": "11:15", "open": 2141.20, "close": 2144.40, "high": 2149.20, "low": 2139.50},  # GREEN
    {"time": "11:30", "open": 2144.90, "close": 2144.50, "high": 2145.40, "low": 2140.30},  # RED
    {"time": "11:45", "open": 2144.20, "close": 2142.90, "high": 2144.40, "low": 2141.20},  # RED
    {"time": "12:00", "open": 2143.00, "close": 2141.30, "high": 2143.50, "low": 2141.00},  # RED
    {"time": "12:15", "open": 2141.80, "close": 2143.20, "high": 2145.30, "low": 2140.40},  # GREEN
    {"time": "12:30", "open": 2143.40, "close": 2141.70, "high": 2145.30, "low": 2141.70},  # RED
    {"time": "12:45", "open": 2141.70, "close": 2135.60, "high": 2141.80, "low": 2133.70},  # RED
    {"time": "13:00", "open": 2134.90, "close": 2135.30, "high": 2137.20, "low": 2134.40},  # GREEN
    {"time": "13:15", "open": 2135.60, "close": 2122.90, "high": 2137.10, "low": 2121.00},  # RED
    {"time": "13:30", "open": 2122.90, "close": 2123.30, "high": 2124.10, "low": 2121.10},  # GREEN
    {"time": "13:45", "open": 2123.30, "close": 2123.20, "high": 2124.90, "low": 2121.40},  # RED
    {"time": "14:00", "open": 2123.20, "close": 2121.50, "high": 2124.80, "low": 2121.10},  # RED
    {"time": "14:15", "open": 2121.50, "close": 2122.50, "high": 2123.60, "low": 2121.50},  # GREEN
    {"time": "14:30", "open": 2122.50, "close": 2129.20, "high": 2129.20, "low": 2122.50},  # GREEN
    {"time": "14:45", "open": 2129.10, "close": 2131.20, "high": 2131.90, "low": 2127.10},  # GREEN
    {"time": "15:00", "open": 2131.30, "close": 2141.00, "high": 2141.00, "low": 2128.30},  # GREEN
    # 15:15 candle is still forming, so not included in closed candles
]

print("=" * 80)
print("DALBHARAT 15-min Analysis for Jan 1, 2026")
print("=" * 80)
print(f"\nTotal closed candles: {len(candles_today)}")
print("\nCandles:")
for i, c in enumerate(candles_today, 1):
    color = "GREEN" if c["close"] > c["open"] else "RED"
    print(f"{i:2d}. [{c['time']}] O={c['open']:.2f}, C={c['close']:.2f} [{color:5s}]")

print("\n" + "=" * 80)
print("CALCULATING BLOCKS")
print("=" * 80)

blocks = calculate_15min_blocks(candles_today)

print(f"\nTotal blocks: {len(blocks)}\n")

for idx, block in enumerate(blocks, 1):
    print(f"Block {idx}: {block['direction']} trend")
    print(f"  Candles: {len(block['candles'])}")
    print(f"  Start time: {block['candles'][0]['time']}")
    print(f"  End time: {block['candles'][-1]['time']}")
    print(f"  Start price: {block['start_price']:.2f}")
    print(f"  Low: {block['low']:.2f}")
    print(f"  High: {block['high']:.2f}")
    print(f"  POWER: {block['power']:.2f}")
    print()

print("=" * 80)
print("BIGGEST TREND")
print("=" * 80)

biggest = get_biggest_trend(blocks)
if biggest:
    print(f"\nDirection: {biggest['direction']}")
    print(f"Power: {biggest['power']:.2f}")
    print(f"Time range: {biggest['candles'][0]['time']} to {biggest['candles'][-1]['time']}")
    print(f"Price range: Low={biggest['low']:.2f}, High={biggest['high']:.2f}")
else:
    print("\nNo blocks found")

print("\n" + "=" * 80)
print("USER'S EXPECTED CALCULATION")
print("=" * 80)
print("\nUser says:")
print("  3rd candle (09:45) has open = 2146.40 (Actually 2148.30 from data)")
print("  Next red candle closes at 2118.80")
print("  Power = 2146.40 - 2118.80 = 27.6")
print("\nLet me check the actual data:")
print(f"  Candle 2 (09:30): O={candles_today[1]['open']:.2f} [RED]")
print(f"  Candle 3 (09:45): O={candles_today[2]['open']:.2f} [RED]")
print(f"  Candle 4 (10:00): C={candles_today[3]['close']:.2f} [RED]")
print(f"\nActually, looking at 09:30 candle: O=2147.30")
print(f"And 10:00 candle: C=2118.80")
print(f"Difference: 2147.30 - 2118.80 = {2147.30 - 2118.80:.2f}")
