"""Test the ACTUAL IRB issue - first candle is GREEN 42.20/42.39"""

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
    print(f"   current_block[0] = {candles[0]}")
    print("=" * 100)
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        previous_color = "GREEN" if is_green(previous_candle) else "RED"
        
        print(f"\n🔵 Candle {i+1}: O={current_candle['open']:.2f} C={current_candle['close']:.2f} [{current_color}]")
        print(f"   Current block direction: {current_direction}, Current block size: {len(current_block)}")
        
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
                    print(f"      ❌ NO. Continue UP block")
            elif current_direction == "DOWN" and current_color == "GREEN":
                print(f"      Checking: GREEN close ({current_candle['close']:.2f}) > RED open ({previous_candle['open']:.2f})?")
                if current_candle["close"] > previous_candle["open"]:
                    print(f"      ✅ YES! Trend changes from DOWN to UP")
                    trend_changed = True
                else:
                    print(f"      ❌ NO. Continue DOWN block")
            
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
                    print(f"      📦 Block #{len(blocks)} saved: {current_direction}, start_price={current_block[0]['open']:.2f}")
                
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
            blocks.append({
                "candles": current_block,
                "direction": current_direction,
                "power": max(block_opens_closes) - min(block_opens_closes),
                "start_price": current_block[0]["open"],
                "low": min(block_opens_closes),
                "high": max(block_opens_closes)
            })
            print(f"\n📦 Final block #{len(blocks)} saved: {current_direction}, start_price={current_block[0]['open']:.2f}")
    
    return blocks

print("\n" + "=" * 100)
print("IRB STOCK - ACTUAL SCENARIO (First candle is GREEN)")
print("=" * 100)
print("\nUser's Report:")
print("  First candle: 42.20/42.39 (GREEN)")
print("  ❌ Showing starting candle as: 42.34/42.37")
print("  ✅ Should show: 42.20/42.39")
print("=" * 100)

# Scenario: First candle is GREEN 42.20/42.39
# Let me create different scenarios to see when 42.34/42.37 would be shown as start

# Scenario 1: All GREEN candles
print("\n\n📊 SCENARIO 1: All GREEN candles (continuous UP trend)")
print("-" * 100)
irb_scenario1 = [
    {"idx": 1, "open": 42.20, "close": 42.39},  # GREEN
    {"idx": 2, "open": 42.34, "close": 42.37},  # GREEN
    {"idx": 3, "open": 42.35, "close": 42.50},  # GREEN
]

blocks1 = calculate_15min_blocks(irb_scenario1)
print("\n\nResult:")
for idx, block in enumerate(blocks1, 1):
    print(f"Block {idx}: {block['direction']}, Power={block['power']:.2f}")
    print(f"  Start price: {block['start_price']:.2f} (from candle #{block['candles'][0]['idx']})")
    
biggest1 = max(blocks1, key=lambda b: b['power'])
print(f"\nBiggest trend starts from: {biggest1['start_price']:.2f}")
if biggest1['start_price'] == 42.20:
    print("✅ CORRECT: Shows 42.20")
else:
    print(f"❌ WRONG: Shows {biggest1['start_price']:.2f} instead of 42.20")

# Scenario 2: First GREEN is small, then bigger GREEN candles
print("\n\n" + "=" * 100)
print("📊 SCENARIO 2: Mix of RED and GREEN with first being GREEN")
print("-" * 100)
irb_scenario2 = [
    {"idx": 1, "open": 42.20, "close": 42.39},  # GREEN
    {"idx": 2, "open": 42.38, "close": 42.30},  # RED (small)
    {"idx": 3, "open": 42.34, "close": 42.37},  # GREEN
    {"idx": 4, "open": 42.35, "close": 42.80},  # GREEN (big)
]

blocks2 = calculate_15min_blocks(irb_scenario2)
print("\n\nResult:")
for idx, block in enumerate(blocks2, 1):
    print(f"Block {idx}: {block['direction']}, Power={block['power']:.2f}, Candles={len(block['candles'])}")
    print(f"  Start price: {block['start_price']:.2f} (from candle #{block['candles'][0]['idx']})")
    
biggest2 = max(blocks2, key=lambda b: b['power'])
print(f"\nBiggest trend starts from: {biggest2['start_price']:.2f} (candle #{biggest2['candles'][0]['idx']})")
if biggest2['start_price'] == 42.34:
    print(f"❌ This matches the bug! Biggest trend shows 42.34 instead of the FIRST GREEN candle at 42.20")
    print(f"   The first GREEN candle (42.20/42.39) is in a different block")
