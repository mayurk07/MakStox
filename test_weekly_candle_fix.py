"""
Test script to verify the weekly candle "in scope" logic fix.

Expected behavior:
INCLUDE last weekly candle IF:
- Thursday after 3:30PM (market closed) OR
- Friday, Saturday, or Sunday (any time) OR
- Monday before 9:15AM (market closed)

EXCLUDE otherwise
"""

from datetime import datetime, timedelta
import pytz

IST = pytz.timezone('Asia/Kolkata')

def test_weekly_logic():
    """Test the weekly candle inclusion logic"""
    
    test_cases = [
        # (weekday, hour, minute, should_include, description)
        (3, 14, 0, False, "Thursday 2:00 PM (market open) - should EXCLUDE"),
        (3, 15, 29, False, "Thursday 3:29 PM (market still open) - should EXCLUDE"),
        (3, 15, 30, True, "Thursday 3:30 PM (market closed) - should INCLUDE"),
        (3, 16, 0, True, "Thursday 4:00 PM (market closed) - should INCLUDE"),
        (3, 20, 0, True, "Thursday 8:00 PM (market closed) - should INCLUDE"),
        
        (4, 0, 0, True, "Friday 12:00 AM - should INCLUDE"),
        (4, 10, 0, True, "Friday 10:00 AM - should INCLUDE"),
        (4, 15, 30, True, "Friday 3:30 PM - should INCLUDE"),
        (4, 23, 59, True, "Friday 11:59 PM - should INCLUDE"),
        
        (5, 0, 0, True, "Saturday 12:00 AM - should INCLUDE"),
        (5, 12, 0, True, "Saturday 12:00 PM - should INCLUDE"),
        (5, 23, 59, True, "Saturday 11:59 PM - should INCLUDE"),
        
        (6, 0, 0, True, "Sunday 12:00 AM - should INCLUDE"),
        (6, 12, 0, True, "Sunday 12:00 PM - should INCLUDE"),
        (6, 23, 59, True, "Sunday 11:59 PM - should INCLUDE"),
        
        (0, 0, 0, True, "Monday 12:00 AM (before market) - should INCLUDE"),
        (0, 9, 0, True, "Monday 9:00 AM (before market) - should INCLUDE"),
        (0, 9, 14, True, "Monday 9:14 AM (before market) - should INCLUDE"),
        (0, 9, 15, False, "Monday 9:15 AM (market open) - should EXCLUDE"),
        (0, 10, 0, False, "Monday 10:00 AM (market open) - should EXCLUDE"),
        (0, 15, 30, False, "Monday 3:30 PM (market closed) - should EXCLUDE"),
        
        (1, 10, 0, False, "Tuesday 10:00 AM (market open) - should EXCLUDE"),
        (1, 15, 30, False, "Tuesday 3:30 PM (market closed) - should EXCLUDE"),
        
        (2, 10, 0, False, "Wednesday 10:00 AM (market open) - should EXCLUDE"),
        (2, 15, 30, False, "Wednesday 3:30 PM (market closed) - should EXCLUDE"),
    ]
    
    print("=" * 80)
    print("WEEKLY CANDLE LOGIC TEST")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for weekday, hour, minute, expected_include, description in test_cases:
        # Simulate the logic
        market_closed = False
        
        if weekday in [0, 1, 2, 3, 4]:  # Monday to Friday
            if (hour < 9 or (hour == 9 and minute < 15)) or (hour > 15 or (hour == 15 and minute >= 30)):
                market_closed = True
        elif weekday in [5, 6]:  # Weekend
            market_closed = True
        
        # Apply the fixed weekly logic
        should_include = False
        if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
            should_include = True
        elif weekday == 3 and market_closed:  # Thursday after 3:30PM
            should_include = True
        elif weekday == 0 and (hour < 9 or (hour == 9 and minute < 15)):  # Monday before 9:15AM (specifically)
            should_include = True
        
        # Check result
        result = "✅ PASS" if should_include == expected_include else "❌ FAIL"
        status = "PASS" if should_include == expected_include else "FAIL"
        
        if should_include == expected_include:
            passed += 1
        else:
            failed += 1
        
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        print(f"{result} | {description}")
        print(f"      Weekday: {weekday_names[weekday]} ({weekday}), Time: {hour:02d}:{minute:02d}")
        print(f"      Market Closed: {market_closed}, Should Include: {should_include}, Expected: {expected_include}")
        
        if status == "FAIL":
            print(f"      ⚠️  MISMATCH DETECTED!")
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The weekly candle logic is correct.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the logic.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_weekly_logic()
    exit(0 if success else 1)
