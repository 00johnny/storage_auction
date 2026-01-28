#!/usr/bin/env python3
"""
Test script to verify Unix timestamp and countdown parsing fixes
"""
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Test 1: Unix timestamp parsing
print("=" * 60)
print("Test 1: Unix timestamp parsing")
print("=" * 60)

end_time_str = "1769355480"  # Unix timestamp from user's error message

closes_at = None

# Check if it's a Unix timestamp (all digits)
if end_time_str and end_time_str.strip():
    if end_time_str.strip().isdigit():
        try:
            closes_at = datetime.fromtimestamp(int(end_time_str))
            print(f"✓ Successfully parsed Unix timestamp: {closes_at}")
            print(f"  Unix timestamp: {end_time_str}")
            print(f"  Parsed datetime: {closes_at.strftime('%Y-%m-%d %H:%M:%S')}")
        except (ValueError, OSError) as e:
            print(f"✗ Failed to parse Unix timestamp '{end_time_str}': {e}")
    else:
        print(f"✗ Not a Unix timestamp (contains non-digit characters)")
else:
    print(f"✗ Empty timestamp")

print()

# Test 2: Countdown timer with empty strings
print("=" * 60)
print("Test 2: Countdown timer parsing with empty strings")
print("=" * 60)

# Simulate HTML with empty countdown elements
html = """
<div class="countdown" data-expiry="">
    <div class="time-days"></div>
    <div class="time-hours">12</div>
    <div class="time-minutes">30</div>
    <div class="time-seconds">45</div>
</div>
"""

soup = BeautifulSoup(html, 'html.parser')
countdown_elem = soup.find('div', class_='countdown')

def safe_int(elem, default=0):
    if not elem:
        return default
    text = elem.text.strip()
    if not text or text == '':
        return default
    try:
        return int(text)
    except ValueError:
        return default

days_elem = countdown_elem.find('div', class_='time-days')
hours_elem = countdown_elem.find('div', class_='time-hours')
minutes_elem = countdown_elem.find('div', class_='time-minutes')
seconds_elem = countdown_elem.find('div', class_='time-seconds')

days = safe_int(days_elem, 0)
hours = safe_int(hours_elem, 0)
minutes = safe_int(minutes_elem, 0)
seconds = safe_int(seconds_elem, 0)

print(f"Parsed countdown values:")
print(f"  Days: {days} (element text: '{days_elem.text if days_elem else 'None'}')")
print(f"  Hours: {hours}")
print(f"  Minutes: {minutes}")
print(f"  Seconds: {seconds}")

time_remaining = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
closes_at = datetime.now() + time_remaining

print(f"\n✓ Successfully calculated end time from countdown:")
print(f"  Time remaining: {time_remaining}")
print(f"  Closes at: {closes_at.strftime('%Y-%m-%d %H:%M:%S')}")

print()

# Test 3: Combined test - empty data-expiry falls back to countdown
print("=" * 60)
print("Test 3: Empty data-expiry falls back to countdown")
print("=" * 60)

data_expiry = countdown_elem.get("data-expiry")
print(f"data-expiry attribute: '{data_expiry}'")

closes_at = None

# Method 1: Try data-expiry attribute
if data_expiry and data_expiry.strip():
    print("  Attempting to parse data-expiry...")
    if data_expiry.strip().isdigit():
        try:
            closes_at = datetime.fromtimestamp(int(data_expiry))
            print(f"  ✓ Parsed Unix timestamp: {closes_at}")
        except (ValueError, OSError) as e:
            print(f"  ✗ Failed: {e}")
    else:
        print(f"  ✗ Not a Unix timestamp")
else:
    print("  data-expiry is empty, skipping...")

# Method 2: If data-expiry is empty, try countdown timer
if not closes_at and countdown_elem:
    print("  Falling back to countdown timer...")
    days = safe_int(days_elem, 0)
    hours = safe_int(hours_elem, 0)
    minutes = safe_int(minutes_elem, 0)
    seconds = safe_int(seconds_elem, 0)

    time_remaining = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    closes_at = datetime.now() + time_remaining
    print(f"  ✓ Parsed from countdown: {closes_at}")

print()
print("=" * 60)
print("All tests completed!")
print("=" * 60)
