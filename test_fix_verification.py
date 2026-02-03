"""
Comprehensive test to verify the 15-min biggest trend fix for DALBHARAT
"""

def is_green(candle):
    return candle["close"] > candle["open"]

def calculate_15min_blocks(candles):
    """
    New simplified logic for 15-min biggest trend blocks.
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
        
        if current_direction == "UP" and current_color == "GREEN":
            current_block.append(current_candle)
        elif current_direction == "DOWN" and current_color == "RED":
            current_block.append(current_candle)
        else:
            trend_changed = False
            
            if current_direction == "UP" and current_color == "RED":
                if current_candle["close"] < previous_candle["open"]:
                    trend_changed = True
            elif current_direction == "DOWN" and current_color == "GREEN":
                if current_candle["close"] > previous_candle["open"]:
                    trend_changed = True
            
            if trend_changed:
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
                
                current_block = [current_candle]
                current_direction = "UP" if current_color == "GREEN" else "DOWN"
            else:
                current_block.append(current_candle)
    
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

def run_test():
    """Run test with DALBHARAT data"""
    
    # Test data - DALBHARAT Jan 1, 2026
    candles = [
        {"time": "09:15", "open": 2132.90, "close": 2147.50},  # GREEN
        {"time": "09:30", "open": 2147.30, "close": 2146.40},  # RED
        {"time": "09:45", "open": 2148.30, "close": 2122.30},  # RED - BIG DROP!
        {"time": "10:00", "open": 2123.70, "close": 2118.80},  # RED
        {"time": "10:15", "open": 2120.10, "close": 2119.10},  # RED
        {"time": "10:30", "open": 2120.00, "close": 2122.70},  # GREEN
    ]
    
    blocks = calculate_15min_blocks(candles)
    
    print("=" * 80)
    print("TEST: DALBHARAT 15-min Biggest Trend Fix")
    print("=" * 80)
    
    print("\n✅ TEST 1: Check that DOWN block is created correctly")
    print("-" * 80)
    
    # Find the DOWN block
    down_blocks = [b for b in blocks if b["direction"] == "DOWN"]
    
    if len(down_blocks) > 0:
        down_block = down_blocks[0]
        print(f"✓ DOWN block found!")
        print(f"  Time range: {down_block['candles'][0]['time']} to {down_block['candles'][-1]['time']}")
        print(f"  Expected: 09:45 to 10:15")
        
        # Check if it starts at 09:45
        if down_block['candles'][0]['time'] == "09:45":
            print(f"  ✓ Correctly starts at 09:45")
        else:
            print(f"  ✗ ERROR: Starts at {down_block['candles'][0]['time']}, expected 09:45")
            
        # Check if it includes the big drop
        if down_block['power'] > 25:
            print(f"  ✓ Power is {down_block['power']:.2f} (captures the big drop)")
        else:
            print(f"  ✗ ERROR: Power is only {down_block['power']:.2f}, should be > 25")
            
        # Check support price
        if down_block['start_price'] == 2148.30:
            print(f"  ✓ Support price is {down_block['start_price']:.2f} (opening of 09:45)")
        else:
            print(f"  ✗ ERROR: Support price is {down_block['start_price']:.2f}, expected 2148.30")
    else:
        print("✗ ERROR: No DOWN block found!")
    
    print("\n✅ TEST 2: Check that 09:45 RED candle is NOT in UP block")
    print("-" * 80)
    
    up_blocks = [b for b in blocks if b["direction"] == "UP"]
    
    if len(up_blocks) > 0:
        first_up_block = up_blocks[0]
        
        # Check that first UP block ends before 09:45
        last_time = first_up_block['candles'][-1]['time']
        if last_time < "09:45":
            print(f"✓ First UP block ends at {last_time} (before 09:45)")
        else:
            print(f"✗ ERROR: First UP block extends to {last_time}, should end before 09:45")
    
    print("\n✅ TEST 3: Verify biggest trend is DOWN")
    print("-" * 80)
    
    if blocks:
        max_power = max(b["power"] for b in blocks)
        biggest = next(b for b in blocks if b["power"] == max_power)
        
        if biggest["direction"] == "DOWN":
            print(f"✓ Biggest trend is DOWN (power: {biggest['power']:.2f})")
            print(f"  Time: {biggest['candles'][0]['time']} to {biggest['candles'][-1]['time']}")
            print(f"  Support: {biggest['start_price']:.2f}")
        else:
            print(f"✗ ERROR: Biggest trend is {biggest['direction']}, expected DOWN")
    
    print("\n" + "=" * 80)
    print("All Blocks:")
    print("=" * 80)
    for idx, block in enumerate(blocks, 1):
        print(f"\nBlock {idx}: {block['direction']}")
        print(f"  Time: {block['candles'][0]['time']} to {block['candles'][-1]['time']}")
        print(f"  Power: {block['power']:.2f}")
        print(f"  Support: {block['start_price']:.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ OLD LOGIC (WRONG):")
    print("   - Biggest trend: UP (power 26.00)")
    print("   - Block 1 (UP): 09:15, 09:30, 09:45 ← Wrong! Includes big RED drop")
    print("\n✅ NEW LOGIC (CORRECT):")
    if blocks:
        biggest = next(b for b in blocks if b["power"] == max(b["power"] for b in blocks))
        print(f"   - Biggest trend: {biggest['direction']} (power {biggest['power']:.2f})")
        print(f"   - Block starts at {biggest['candles'][0]['time']} ← Correct!")
        print(f"   - Support price: {biggest['start_price']:.2f}")

if __name__ == "__main__":
    run_test()
