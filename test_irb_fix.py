"""Test the proposed fix for IRB bug"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_15min_blocks_FIXED(candles):
    """FIXED implementation - compare with previous candle's CLOSE, not OPEN"""
    if not candles or len(candles) < 1:
        return []
    
    blocks = []
    current_block = [candles[0]]
    current_direction = "UP" if is_green(candles[0]) else "DOWN"
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        
        # Check if candle color matches current block direction
        if current_direction == "UP" and current_color == "GREEN":
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            current_block.append(current_candle)
        else:
            # Opposite color - check if trend actually changes
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                # Was UP (previous GREEN), now RED
                # Check if RED close < GREEN CLOSE (not GREEN open!)
                if current_candle["close"] < previous_candle["close"]:
                    trend_changed = True
            elif current_direction == "DOWN" and current_color == "GREEN":
                # Was DOWN (previous RED), now GREEN
                # Check if GREEN close > RED CLOSE (not RED open!)
                if current_candle["close"] > previous_candle["close"]:
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

print("=" * 100)
print("IRB BUG FIX VERIFICATION")
print("=" * 100)

# The scenario that triggers the bug:
irb_candles = [
    {"idx": 1, "open": 42.50, "close": 42.10},  # RED - DOWN
    {"idx": 2, "open": 42.20, "close": 42.39},  # GREEN - should start UP trend
    {"idx": 3, "open": 42.34, "close": 42.37},  # GREEN
    {"idx": 4, "open": 42.35, "close": 42.80},  # GREEN
    {"idx": 5, "open": 42.78, "close": 43.20},  # GREEN
]

print("\n📊 Test Data:")
for c in irb_candles:
    color = "GREEN" if is_green(c) else "RED"
    print(f"   Candle #{c['idx']}: {c['open']:.2f}/{c['close']:.2f} [{color}]")

print("\n" + "-" * 100)
print("TESTING FIXED LOGIC")
print("-" * 100)

blocks_fixed = calculate_15min_blocks_FIXED(irb_candles)

print("\nBlocks found:")
for idx, block in enumerate(blocks_fixed, 1):
    print(f"\nBlock {idx}: {block['direction']}, Power: {block['power']:.2f}")
    candles_in_block = block['candles']
    print(f"  First candle #{candles_in_block[0]['idx']}: O={candles_in_block[0]['open']:.2f} C={candles_in_block[0]['close']:.2f}")
    print(f"  Last candle #{candles_in_block[-1]['idx']}: O={candles_in_block[-1]['open']:.2f} C={candles_in_block[-1]['close']:.2f}")
    print(f"  Total candles: {len(candles_in_block)}")

biggest_fixed = max(blocks_fixed, key=lambda b: b['power'])
print(f"\n🔍 Biggest trend: {biggest_fixed['direction']}, Power: {biggest_fixed['power']:.2f}")
print(f"   Starting candle #{biggest_fixed['candles'][0]['idx']}: {biggest_fixed['candles'][0]['open']:.2f}/{biggest_fixed['candles'][0]['close']:.2f}")

print("\n" + "=" * 100)
print("VERIFICATION")
print("=" * 100)

if biggest_fixed['candles'][0]['idx'] == 2 and biggest_fixed['candles'][0]['open'] == 42.20:
    print("\n✅ BUG FIXED!")
    print("   Biggest trend now correctly starts from candle #2 (42.20/42.39)")
    print("   This is the first GREEN candle, which should start the UP trend")
else:
    print("\n❌ Fix didn't work")
    print(f"   Still starting from candle #{biggest_fixed['candles'][0]['idx']}")

print("\n" + "-" * 100)
print("EXPLANATION OF THE FIX")
print("-" * 100)
print("\n❌ OLD LOGIC (BUGGY):")
print("   When checking DOWN to UP transition:")
print("   - Check: GREEN close > RED open")
print("   - For candle #2: 42.39 > 42.50? NO")
print("   - Result: Candle #2 stays in DOWN block ❌")

print("\n✅ NEW LOGIC (FIXED):")
print("   When checking DOWN to UP transition:")
print("   - Check: GREEN close > RED CLOSE")
print("   - For candle #2: 42.39 > 42.10? YES")
print("   - Result: Trend changes! Candle #2 starts new UP block ✅")

print("\n📝 Why this makes sense:")
print("   - RED candle went from 42.50 → 42.10 (downward)")
print("   - GREEN candle went from 42.20 → 42.39 (upward)")
print("   - GREEN close (42.39) is ABOVE RED close (42.10)")
print("   - This indicates the downtrend has reversed to an uptrend")
