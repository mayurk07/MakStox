"""Test the new 15-min block calculation logic with DALBHARAT data"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_15min_blocks_new(candles):
    """
    New simplified logic for 15-min biggest trend blocks.
    
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
    
    print(f"\nStarting with candle 1: {candles[0]['time']} [{'GREEN' if is_green(candles[0]) else 'RED'}]")
    print(f"Initial direction: {current_direction}")
    print("=" * 80)
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        previous_color = "GREEN" if is_green(previous_candle) else "RED"
        
        print(f"\nCandle {i+1}: {current_candle['time']} [{current_color}]")
        print(f"  Previous: {previous_candle['time']} [{previous_color}]")
        print(f"  Current block direction: {current_direction}")
        
        # Check if candle color matches current block direction
        if current_direction == "UP" and current_color == "GREEN":
            # Same color, continue block
            print(f"  → Same color (GREEN), continue UP block")
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            # Same color, continue block
            print(f"  → Same color (RED), continue DOWN block")
            current_block.append(current_candle)
        else:
            # Opposite color - check if trend actually changes
            print(f"  → Opposite color detected!")
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                # Was UP (previous GREEN), now RED - check if RED close < GREEN open
                print(f"     Checking: RED close ({current_candle['close']:.2f}) < GREEN open ({previous_candle['open']:.2f})?")
                if current_candle["close"] < previous_candle["open"]:
                    print(f"     ✓ YES! Trend changes from UP to DOWN")
                    trend_changed = True
                else:
                    print(f"     ✗ NO. Continue UP block")
            elif current_direction == "DOWN" and current_color == "GREEN":
                # Was DOWN (previous RED), now GREEN - check if GREEN close > RED open
                print(f"     Checking: GREEN close ({current_candle['close']:.2f}) > RED open ({previous_candle['open']:.2f})?")
                if current_candle["close"] > previous_candle["open"]:
                    print(f"     ✓ YES! Trend changes from DOWN to UP")
                    trend_changed = True
                else:
                    print(f"     ✗ NO. Continue DOWN block")
            
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
                    print(f"     📦 Block saved: {current_block[0]['time']} to {current_block[-1]['time']} ({current_direction}, power={blocks[-1]['power']:.2f})")
                
                # Start new block
                current_block = [current_candle]
                current_direction = "UP" if current_color == "GREEN" else "DOWN"
                print(f"     🆕 New block started: {current_direction}")
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
            print(f"\n📦 Final block saved: {current_block[0]['time']} to {current_block[-1]['time']} ({current_direction}, power={blocks[-1]['power']:.2f})")
    
    return blocks

# DALBHARAT candles for Jan 1, 2026 (first 10 candles)
candles_today = [
    {"time": "09:15", "open": 2132.90, "close": 2147.50, "high": 2147.50, "low": 2132.90},  # 1. GREEN
    {"time": "09:30", "open": 2147.30, "close": 2146.40, "high": 2159.70, "low": 2146.40},  # 2. RED
    {"time": "09:45", "open": 2148.30, "close": 2122.30, "high": 2150.50, "low": 2122.30},  # 3. RED
    {"time": "10:00", "open": 2123.70, "close": 2118.80, "high": 2123.70, "low": 2118.50},  # 4. RED
    {"time": "10:15", "open": 2120.10, "close": 2119.10, "high": 2122.30, "low": 2110.50},  # 5. RED
    {"time": "10:30", "open": 2120.00, "close": 2122.70, "high": 2124.80, "low": 2115.70},  # 6. GREEN
    {"time": "10:45", "open": 2122.60, "close": 2126.60, "high": 2128.30, "low": 2122.30},  # 7. GREEN
    {"time": "11:00", "open": 2126.20, "close": 2142.20, "high": 2144.80, "low": 2126.20},  # 8. GREEN
    {"time": "11:15", "open": 2141.20, "close": 2144.40, "high": 2149.20, "low": 2139.50},  # 9. GREEN
    {"time": "11:30", "open": 2144.90, "close": 2144.50, "high": 2145.40, "low": 2140.30},  # 10. RED
]

print("=" * 80)
print("DALBHARAT 15-min Block Calculation - NEW LOGIC")
print("=" * 80)

blocks = calculate_15min_blocks_new(candles_today)

print("\n" + "=" * 80)
print("FINAL BLOCKS SUMMARY")
print("=" * 80)

for idx, block in enumerate(blocks, 1):
    print(f"\nBlock {idx}: {block['direction']}")
    print(f"  Time range: {block['candles'][0]['time']} to {block['candles'][-1]['time']}")
    print(f"  Number of candles: {len(block['candles'])}")
    print(f"  Start price (Support): {block['start_price']:.2f}")
    print(f"  Power: {block['power']:.2f}")
    print(f"  Range: Low={block['low']:.2f}, High={block['high']:.2f}")

print("\n" + "=" * 80)
print("BIGGEST TREND")
print("=" * 80)

if blocks:
    max_power = max(b["power"] for b in blocks)
    biggest = None
    for b in blocks:
        if b["power"] == max_power:
            biggest = b
            break
    
    if biggest:
        print(f"\n✅ Biggest Trend: {biggest['direction']}")
        print(f"   Power: {biggest['power']:.2f}")
        print(f"   Time range: {biggest['candles'][0]['time']} to {biggest['candles'][-1]['time']}")
        print(f"   Support Price: {biggest['start_price']:.2f} (opening price of {biggest['candles'][0]['time']})")
        print(f"   Price range: Low={biggest['low']:.2f}, High={biggest['high']:.2f}")

print("\n" + "=" * 80)
print("EXPECTED vs ACTUAL")
print("=" * 80)
print("\nUser's expectation:")
print("  - DOWN trend from 09:30 to 10:00 (or 10:15)")
print("  - Power: ~28.50 (2147.30 - 2118.80)")
print("  - Support: Opening price of the candle that started this block")
print("\nOld logic result:")
print("  - UP trend (Block 1: 09:15, 09:30, 09:45)")
print("  - Power: 26.00")
print("  - ✗ WRONG!")
