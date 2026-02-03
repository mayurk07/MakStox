"""Test script to find the actual IRB bug - more complex scenario"""

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
    
    for i in range(1, len(candles)):
        current_candle = candles[i]
        previous_candle = candles[i - 1]
        current_color = "GREEN" if is_green(current_candle) else "RED"
        previous_color = "GREEN" if is_green(previous_candle) else "RED"
        
        # Check if candle color matches current block direction
        if current_direction == "UP" and current_color == "GREEN":
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            current_block.append(current_candle)
        else:
            # Opposite color - check if trend actually changes
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                if current_candle["close"] < previous_candle["open"]:
                    trend_changed = True
            elif current_direction == "DOWN" and current_color == "GREEN":
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

print("\n" + "=" * 100)
print("IRB STOCK - SCENARIO WHERE FIRST CANDLE COULD BE SKIPPED")
print("=" * 100)

# Scenario: What if the first candle is RED and small, 
# then we have a big UP trend starting from the second candle?
# User says: first candle should be 42.20/42.39 (GREEN)
# But it's showing 42.34/42.37 (also GREEN)

# Let me create a scenario where:
# 1. First candle: 42.20/42.39 (GREEN) - small
# 2. Second candle: 42.34/42.37 (GREEN) - small
# 3-6: More GREEN candles making a big UP trend
# Then a down trend

irb_candles_scenario1 = [
    {"idx": 1, "open": 42.20, "close": 42.39},  # Candle 1: GREEN (+0.19)
    {"idx": 2, "open": 42.34, "close": 42.37},  # Candle 2: GREEN (+0.03) - small
    {"idx": 3, "open": 42.35, "close": 42.80},  # Candle 3: GREEN (+0.45)
    {"idx": 4, "open": 42.78, "close": 43.20},  # Candle 4: GREEN (+0.42)
    {"idx": 5, "open": 43.18, "close": 43.50},  # Candle 5: GREEN (+0.32)
    {"idx": 6, "open": 43.48, "close": 43.20},  # Candle 6: RED (-0.28)
    {"idx": 7, "open": 43.15, "close": 42.80},  # Candle 7: RED (-0.35)
]

print("\nTest Scenario 1: All UP trend candles should be in one block")
print("-" * 100)

blocks1 = calculate_15min_blocks(irb_candles_scenario1)

print("\nBlocks found:")
for idx, block in enumerate(blocks1, 1):
    print(f"\nBlock {idx}: {block['direction']}, Power: {block['power']:.2f}")
    print(f"  First candle #{block['candles'][0]['idx']}: O={block['candles'][0]['open']:.2f} C={block['candles'][0]['close']:.2f}")
    print(f"  Last candle #{block['candles'][-1]['idx']}: O={block['candles'][-1]['open']:.2f} C={block['candles'][-1]['close']:.2f}")
    print(f"  Total candles: {len(block['candles'])}")

biggest1 = max(blocks1, key=lambda b: b['power'])
print(f"\n🔍 Biggest trend: {biggest1['direction']}, Power: {biggest1['power']:.2f}")
print(f"   Start candle #{biggest1['candles'][0]['idx']}: {biggest1['candles'][0]['open']:.2f}/{biggest1['candles'][0]['close']:.2f}")

print("\n" + "=" * 100)
print("SCENARIO 2: What if there's a RED candle first, then the issue happens?")
print("=" * 100)

# Maybe the scenario is:
# 1. First candle is RED  
# 2. Then GREEN candle 42.20/42.39
# 3. But it's not starting properly?

irb_candles_scenario2 = [
    {"idx": 1, "open": 42.50, "close": 42.10},  # Candle 1: RED - down trend
    {"idx": 2, "open": 42.20, "close": 42.39},  # Candle 2: GREEN - should this start new block?
    {"idx": 3, "open": 42.34, "close": 42.37},  # Candle 3: GREEN 
    {"idx": 4, "open": 42.35, "close": 42.80},  # Candle 4: GREEN
    {"idx": 5, "open": 42.78, "close": 43.20},  # Candle 5: GREEN
]

print("\nTest Scenario 2: RED candle first, then GREEN candles")
print("-" * 100)

blocks2 = calculate_15min_blocks(irb_candles_scenario2)

print("\nBlocks found:")
for idx, block in enumerate(blocks2, 1):
    print(f"\nBlock {idx}: {block['direction']}, Power: {block['power']:.2f}")
    print(f"  First candle #{block['candles'][0]['idx']}: O={block['candles'][0]['open']:.2f} C={block['candles'][0]['close']:.2f}")
    print(f"  Last candle #{block['candles'][-1]['idx']}: O={block['candles'][-1]['open']:.2f} C={block['candles'][-1]['close']:.2f}")
    print(f"  Total candles: {len(block['candles'])}")

biggest2 = max(blocks2, key=lambda b: b['power'])
print(f"\n🔍 Biggest trend: {biggest2['direction']}, Power: {biggest2['power']:.2f}")
print(f"   Start candle #{biggest2['candles'][0]['idx']}: {biggest2['candles'][0]['open']:.2f}/{biggest2['candles'][0]['close']:.2f}")

if biggest2['candles'][0]['idx'] == 3 and biggest2['candles'][0]['open'] == 42.34:
    print(f"\n❌ BUG FOUND! Starting from candle #3 (42.34/42.37)")
    print(f"   Should start from candle #2 (42.20/42.39)")
    print(f"\n🔍 Analysis:")
    print(f"   Candle #2 (42.20/42.39) has close=42.39, Candle #1 (RED) has open=42.50")
    print(f"   Check: 42.39 > 42.50? NO! ({42.39} <= {42.50})")
    print(f"   So candle #2 gets added to the DOWN block, not starting a new UP block!")
    print(f"   This is the BUG!")
