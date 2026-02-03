"""Test script to debug IRB biggest trend bug"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_15min_blocks(candles):
    """Current implementation from server.py"""
    if not candles or len(candles) < 1:
        return []
    
    blocks = []
    current_block = [candles[0]]
    current_direction = "UP" if is_green(candles[0]) else "DOWN"
    
    print(f"\n🔵 Starting with candle 1: O={candles[0]['open']:.2f} C={candles[0]['close']:.2f} [{'GREEN' if is_green(candles[0]) else 'RED'}]")
    print(f"   Initial direction: {current_direction}")
    print("=" * 100)
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        previous_color = "GREEN" if is_green(previous_candle) else "RED"
        
        print(f"\n🔵 Candle {i+1}: O={current_candle['open']:.2f} C={current_candle['close']:.2f} [{current_color}]")
        print(f"   Previous candle: O={previous_candle['open']:.2f} C={previous_candle['close']:.2f} [{previous_color}]")
        print(f"   Current block direction: {current_direction}")
        
        # Check if candle color matches current block direction
        if current_direction == "UP" and current_color == "GREEN":
            print(f"   → Same color (GREEN), continue UP block")
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            print(f"   → Same color (RED), continue DOWN block")
            current_block.append(current_candle)
        else:
            print(f"   → Opposite color detected!")
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                print(f"      Checking: RED close ({current_candle['close']:.2f}) < GREEN open ({previous_candle['open']:.2f})?")
                if current_candle["close"] < previous_candle["open"]:
                    print(f"      ✅ YES! Trend changes from UP to DOWN")
                    trend_changed = True
                else:
                    print(f"      ❌ NO ({current_candle['close']:.2f} >= {previous_candle['open']:.2f}). Continue UP block")
            elif current_direction == "DOWN" and current_color == "GREEN":
                print(f"      Checking: GREEN close ({current_candle['close']:.2f}) > RED open ({previous_candle['open']:.2f})?")
                if current_candle["close"] > previous_candle["open"]:
                    print(f"      ✅ YES! Trend changes from DOWN to UP")
                    trend_changed = True
                else:
                    print(f"      ❌ NO ({current_candle['close']:.2f} <= {previous_candle['open']:.2f}). Continue DOWN block")
            
            if trend_changed:
                # Save current block
                block_opens_closes = []
                for c in current_block:
                    block_opens_closes.extend([c["open"], c["close"]])
                
                if block_opens_closes:
                    power = max(block_opens_closes) - min(block_opens_closes)
                    blocks.append({
                        "candles": current_block.copy(),
                        "direction": current_direction,
                        "power": power,
                        "start_price": current_block[0]["open"],
                        "start_candle_open": current_block[0]["open"],
                        "start_candle_close": current_block[0]["close"],
                        "low": min(block_opens_closes),
                        "high": max(block_opens_closes)
                    })
                    print(f"      📦 Block #{len(blocks)} saved: {current_direction}")
                    print(f"         Candles: {len(current_block)} (from candle {i - len(current_block) + 1} to {i})")
                    print(f"         First candle: O={current_block[0]['open']:.2f} C={current_block[0]['close']:.2f}")
                    print(f"         Last candle: O={current_block[-1]['open']:.2f} C={current_block[-1]['close']:.2f}")
                    print(f"         Power: {power:.2f}")
                
                # Start new block
                current_block = [current_candle]
                current_direction = "UP" if current_color == "GREEN" else "DOWN"
                print(f"      🆕 New block started: {current_direction}")
            else:
                current_block.append(current_candle)
    
    # Save the last block
    if current_block:
        block_opens_closes = []
        for c in current_block:
            block_opens_closes.extend([c["open"], c["close"]])
        
        if block_opens_closes:
            power = max(block_opens_closes) - min(block_opens_closes)
            blocks.append({
                "candles": current_block,
                "direction": current_direction,
                "power": power,
                "start_price": current_block[0]["open"],
                "start_candle_open": current_block[0]["open"],
                "start_candle_close": current_block[0]["close"],
                "low": min(block_opens_closes),
                "high": max(block_opens_closes)
            })
            print(f"\n📦 Final block #{len(blocks)} saved: {current_direction}")
            print(f"   Candles: {len(current_block)}")
            print(f"   First candle: O={current_block[0]['open']:.2f} C={current_block[0]['close']:.2f}")
            print(f"   Last candle: O={current_block[-1]['open']:.2f} C={current_block[-1]['close']:.2f}")
            print(f"   Power: {power:.2f}")
    
    return blocks

# IRB test data - simulated candles based on user's bug report
# User says: Currently showing 42.34/42.37 but should be 42.20/42.39
# This means first candle should be 42.20 (open) / 42.39 (close) - GREEN
# But it's showing 42.34/42.37 - which could be the second candle

print("\n" + "=" * 100)
print("IRB STOCK - BIGGEST TREND BUG TEST")
print("=" * 100)
print("\nUser's Report:")
print("  ❌ Currently showing: Starting candle = 42.34 (open) / 42.37 (close)")
print("  ✅ Should show: Starting candle = 42.20 (open) / 42.39 (close) - FIRST candle")
print("=" * 100)

# Simulated IRB candles - creating a scenario where this bug would occur
irb_candles = [
    {"open": 42.20, "close": 42.39},  # Candle 1: GREEN (this should be the start)
    {"open": 42.34, "close": 42.37},  # Candle 2: GREEN (currently being shown as start)
    {"open": 42.35, "close": 42.50},  # Candle 3: GREEN
    {"open": 42.48, "close": 42.55},  # Candle 4: GREEN
    {"open": 42.52, "close": 42.45},  # Candle 5: RED
    {"open": 42.43, "close": 42.40},  # Candle 6: RED
]

blocks = calculate_15min_blocks(irb_candles)

print("\n" + "=" * 100)
print("FINAL BLOCKS SUMMARY")
print("=" * 100)

for idx, block in enumerate(blocks, 1):
    print(f"\n📦 Block {idx}: {block['direction']}")
    print(f"   Number of candles: {len(block['candles'])}")
    print(f"   First candle: O={block['start_candle_open']:.2f} C={block['start_candle_close']:.2f}")
    print(f"   Start price (Support): {block['start_price']:.2f}")
    print(f"   Power: {block['power']:.2f}")

print("\n" + "=" * 100)
print("BIGGEST TREND")
print("=" * 100)

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
        print(f"   Starting candle: O={biggest['start_candle_open']:.2f} C={biggest['start_candle_close']:.2f}")
        print(f"   Support Price: {biggest['start_price']:.2f}")
        
        print("\n" + "=" * 100)
        print("BUG ANALYSIS")
        print("=" * 100)
        
        if biggest['start_candle_open'] == 42.34 and biggest['start_candle_close'] == 42.37:
            print("\n❌ BUG CONFIRMED!")
            print("   The biggest trend is starting from candle 2 (42.34/42.37)")
            print("   It should start from candle 1 (42.20/42.39)")
            print("\n🔍 Root Cause:")
            print("   The first candle (42.20/42.39) is not being included in the biggest trend block")
        elif biggest['start_candle_open'] == 42.20 and biggest['start_candle_close'] == 42.39:
            print("\n✅ BUG FIXED!")
            print("   The biggest trend is correctly starting from candle 1 (42.20/42.39)")
        else:
            print(f"\n⚠️  Different scenario: Starting from {biggest['start_candle_open']:.2f}/{biggest['start_candle_close']:.2f}")
