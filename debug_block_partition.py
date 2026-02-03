"""Deep dive into block partitioning logic to find the bug"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_udts(candles):
    """Calculate UDTS direction"""
    if not candles:
        return {"direction": "UNKNOWN"}
    
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
        # No G1 found
        closed_candles = candles[:-1] if len(candles) > 1 else []
        
        if len(closed_candles) == 0:
            forming_candle = candles[-1]
            direction = "UP" if is_green(forming_candle) else "DOWN"
        else:
            oldest_closed = closed_candles[0]
            newest_closed = closed_candles[-1]
            price_diff = newest_closed["close"] - oldest_closed["open"]
            direction = "UP" if price_diff >= 0 else "DOWN"
        
        return {"direction": direction}
    
    # Find R2 and G2
    r2_idx = None
    for i in range(g1_idx + 1, len(candles)):
        if is_red(candles[i]):
            for j in range(i - 1, -1, -1):
                if is_green(candles[j]):
                    if candles[i]["close"] < candles[j]["open"]:
                        r2_idx = i
                        break
            if r2_idx is not None:
                break
    
    direction = "DOWN" if r2_idx is not None else "UP"
    return {"direction": direction}

# DALBHARAT candles for Jan 1, 2026
candles = [
    {"time": "09:15", "open": 2132.90, "close": 2147.50},  # 1. GREEN
    {"time": "09:30", "open": 2147.30, "close": 2146.40},  # 2. RED
    {"time": "09:45", "open": 2148.30, "close": 2122.30},  # 3. RED
    {"time": "10:00", "open": 2123.70, "close": 2118.80},  # 4. RED
    {"time": "10:15", "open": 2120.10, "close": 2119.10},  # 5. RED
    {"time": "10:30", "open": 2120.00, "close": 2122.70},  # 6. GREEN
]

print("=" * 80)
print("TRACING BLOCK PARTITIONING - First 6 Candles")
print("=" * 80)

# Start with candle 1
current_block = [candles[0]]
current_direction = "UP" if is_green(candles[0]) else "DOWN"
print(f"\nInitial: Block = [Candle 1 (09:15 GREEN)], Direction = {current_direction}")

# Process candle 2
print("\n" + "=" * 80)
print("Adding Candle 2 (09:30 RED)")
print("=" * 80)
test_block = current_block + [candles[1]]
print(f"Test block: [Candle 1 GREEN, Candle 2 RED]")
test_udts = calculate_udts(test_block)
print(f"UDTS direction: {test_udts['direction']}")

# Check G1/R1
print("\nChecking G1/R1:")
print(f"  Candle 1 (GREEN): close={candles[0]['close']:.2f}")
print(f"  Candle 2 (RED): open={candles[1]['open']:.2f}")
print(f"  Is Candle 1 close > Candle 2 open? {candles[0]['close']} > {candles[1]['open']} = {candles[0]['close'] > candles[1]['open']}")
print(f"  Result: G1 = Candle 1, R1 = Candle 2")
print(f"  Since G1 found, check for R2...")
print(f"  No more candles after G1, so R2 = None")
print(f"  Final UDTS: UP (no R2 found)")

if test_udts['direction'] != current_direction:
    print(f"\n⚠️ Direction changed from {current_direction} to {test_udts['direction']}")
    print("→ Save current block and start new block")
    current_block = [candles[1]]
    current_direction = test_udts['direction']
else:
    print(f"\n✓ Direction same ({current_direction}), add to current block")
    current_block.append(candles[1])

print(f"Current block now: {[c['time'] for c in current_block]}")

# Process candle 3
print("\n" + "=" * 80)
print("Adding Candle 3 (09:45 RED)")
print("=" * 80)
test_block = current_block + [candles[2]]
print(f"Test block: {[c['time'] + ' ' + ('GREEN' if is_green(c) else 'RED') for c in test_block]}")
test_udts = calculate_udts(test_block)
print(f"UDTS direction: {test_udts['direction']}")

print("\nChecking G1/R1 in test block:")
for i in range(len(test_block) - 1, -1, -1):
    if is_green(test_block[i]):
        print(f"  Found GREEN at position {i} ({test_block[i]['time']})")
        for j in range(i - 1, -1, -1):
            if is_red(test_block[j]):
                print(f"    Found previous RED at position {j} ({test_block[j]['time']})")
                print(f"    Checking: {test_block[i]['close']:.2f} > {test_block[j]['open']:.2f}?")
                if test_block[i]["close"] > test_block[j]["open"]:
                    print(f"    ✓ Yes! G1 = position {i}, R1 = position {j}")
                    g1_idx = i
                    r1_idx = j
                else:
                    print(f"    ✗ No")
                break
        break

if test_udts['direction'] != current_direction:
    print(f"\n⚠️ Direction changed from {current_direction} to {test_udts['direction']}")
    print("→ Save current block and start new block")
    print(f"\nBLOCK SAVED: {[c['time'] for c in current_block]} - Direction: {current_direction}")
    
    # Calculate power
    block_opens_closes = []
    for c in current_block:
        block_opens_closes.extend([c["open"], c["close"]])
    power = max(block_opens_closes) - min(block_opens_closes)
    print(f"  Power: {power:.2f}")
    print(f"  Opens/closes: {[f'{x:.2f}' for x in block_opens_closes]}")
    print(f"  Max: {max(block_opens_closes):.2f}, Min: {min(block_opens_closes):.2f}")
    
    current_block = [candles[2]]
    current_direction = test_udts['direction']
else:
    print(f"\n✓ Direction same ({current_direction}), add to current block")
    current_block.append(candles[2])

print(f"Current block now: {[c['time'] for c in current_block]}")

print("\n" + "=" * 80)
print("🔍 THE BUG IS HERE!")
print("=" * 80)
print("""
The problem: When we test [GREEN, RED, RED], the UDTS calculates as UP because:
1. It finds G1 = first GREEN, R1 = first RED
2. It looks for R2 after G1
3. The second RED (09:45) is checked: its close (2122.30) vs previous GREEN's open (2132.90)
4. Is 2122.30 < 2132.90? YES!
5. So R2 = second RED, G2 = first GREEN
6. R2 found → Direction = DOWN

Let me verify this:
""")

test_block = [candles[0], candles[1], candles[2]]
print(f"Test block: {[c['time'] for c in test_block]}")
result = calculate_udts(test_block)
print(f"UDTS result: {result['direction']}")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)
print("""
The issue is that when the block partition algorithm tests adding candle 3 (09:45 RED)
to the block [09:15 GREEN, 09:30 RED, 09:45 RED], it should recognize this as a 
DOWNWARD trend starting from 09:30.

But the current logic includes 09:45 RED in the UP block because it tests 
[GREEN, RED] → UP, so it adds the third RED to the UP block.

Then when it tests [GREEN, RED, RED], it gets DOWN, but by this point, the 09:45
candle has already been added to the wrong block!

The correct blocks should be:
- Block 1 (UP): 09:15 GREEN only
- Block 2 (DOWN): 09:30 RED, 09:45 RED, 10:00 RED, 10:15 RED

But the current code creates:
- Block 1 (UP): 09:15 GREEN, 09:30 RED, 09:45 RED
- Block 2 (DOWN): 10:00 RED, 10:15 RED
""")
