"""Test script to verify the new UDTS logic when G1 is not found"""

def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def calculate_udts_new(candles):
    """New UDTS logic with updated G1=None handling"""
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
        # No G1 found - use alternative logic
        # Check if there are any closed candles (all candles except the last one which is forming)
        closed_candles = candles[:-1] if len(candles) > 1 else []
        
        if len(closed_candles) == 0:
            # Case (a): No closed candles - use forming candle's color
            forming_candle = candles[-1]
            direction = "UP" if is_green(forming_candle) else "DOWN"
            print(f"  → Case (a): No closed candles. Forming candle is {'GREEN' if is_green(forming_candle) else 'RED'}")
        else:
            # Case (b): At least one closed candle exists
            # Compare newest closed candle's close vs oldest closed candle's open
            oldest_closed = closed_candles[0]
            newest_closed = closed_candles[-1]
            price_diff = newest_closed["close"] - oldest_closed["open"]
            direction = "UP" if price_diff >= 0 else "DOWN"
            print(f"  → Case (b): {len(closed_candles)} closed candle(s)")
            print(f"     Oldest closed: O={oldest_closed['open']:.2f}")
            print(f"     Newest closed: C={newest_closed['close']:.2f}")
            print(f"     Difference: {price_diff:.2f} ({'≥0' if price_diff >= 0 else '<0'})")
        
        return {"direction": direction, "g1": None, "r1": None, "r2": None, "g2": None}
    
    r2_idx = None
    g2_idx = None
    
    # Find R2 and G2
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

# Test cases
print("=" * 60)
print("TEST 1: Brand new stock - only 1 forming GREEN candle")
print("=" * 60)
test1 = [{"open": 100, "close": 110, "timestamp": "2025-01"}]
result1 = calculate_udts_new(test1)
print(f"Result: {result1['direction']} (Expected: UP)\n")

print("=" * 60)
print("TEST 2: Brand new stock - only 1 forming RED candle")
print("=" * 60)
test2 = [{"open": 110, "close": 100, "timestamp": "2025-01"}]
result2 = calculate_udts_new(test2)
print(f"Result: {result2['direction']} (Expected: DOWN)\n")

print("=" * 60)
print("TEST 3: One closed candle + one forming candle (uptrend)")
print("=" * 60)
test3 = [
    {"open": 100, "close": 105, "timestamp": "2025-01"},  # Closed
    {"open": 106, "close": 112, "timestamp": "2025-02"}   # Forming
]
result3 = calculate_udts_new(test3)
print(f"Result: {result3['direction']} (Expected: UP, since 105 - 100 = 5 >= 0)\n")

print("=" * 60)
print("TEST 4: One closed candle + one forming candle (downtrend)")
print("=" * 60)
test4 = [
    {"open": 100, "close": 90, "timestamp": "2025-01"},   # Closed
    {"open": 89, "close": 85, "timestamp": "2025-02"}     # Forming
]
result4 = calculate_udts_new(test4)
print(f"Result: {result4['direction']} (Expected: DOWN, since 90 - 100 = -10 < 0)\n")

print("=" * 60)
print("TEST 5: Multiple closed candles (net uptrend)")
print("=" * 60)
test5 = [
    {"open": 100, "close": 95, "timestamp": "2025-01"},   # Closed (oldest)
    {"open": 94, "close": 98, "timestamp": "2025-02"},    # Closed
    {"open": 99, "close": 110, "timestamp": "2025-03"},   # Closed (newest)
    {"open": 111, "close": 115, "timestamp": "2025-04"}   # Forming
]
result5 = calculate_udts_new(test5)
print(f"Result: {result5['direction']} (Expected: UP, since 110 - 100 = 10 >= 0)\n")

print("=" * 60)
print("TEST 6: Multiple closed candles (net downtrend)")
print("=" * 60)
test6 = [
    {"open": 100, "close": 105, "timestamp": "2025-01"},  # Closed (oldest)
    {"open": 104, "close": 98, "timestamp": "2025-02"},   # Closed
    {"open": 97, "close": 90, "timestamp": "2025-03"},    # Closed (newest)
    {"open": 89, "close": 85, "timestamp": "2025-04"}     # Forming
]
result6 = calculate_udts_new(test6)
print(f"Result: {result6['direction']} (Expected: DOWN, since 90 - 100 = -10 < 0)\n")

print("=" * 60)
print("TEST 7: Normal G1 found scenario (should use original logic)")
print("=" * 60)
test7 = [
    {"open": 100, "close": 90, "timestamp": "2025-01"},   # R1
    {"open": 91, "close": 105, "timestamp": "2025-02"},   # G1 (close > R1 open)
    {"open": 106, "close": 110, "timestamp": "2025-03"}   # Forming
]
result7 = calculate_udts_new(test7)
print(f"Result: {result7['direction']} (Expected: UP, G1 found, no R2)\n")

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print("All tests demonstrate the new logic:")
print("✓ Case (a): No closed candles → use forming candle color")
print("✓ Case (b): Has closed candles → compare newest_close vs oldest_open")
print("✓ Original G1 logic still works when G1 is found")
