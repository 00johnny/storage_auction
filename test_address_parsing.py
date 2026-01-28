#!/usr/bin/env python3
"""
Test address parsing from Bid13 HTML
"""
from bs4 import BeautifulSoup

# Sample HTML based on Bid13 structure
html = """
<li class="auction-search-result">
    <a class="auction-link-wrapper" data-node-id="12345" href="/auction/12345">
        <span class="title">Unit A101</span>
        <span class="unit-size">10x10</span>
        <div class="auc-current-bid">$150</div>
        <div class="countdown" data-expiry="1769355480">
            <div class="time-days">5</div>
            <div class="time-hours">12</div>
            <div class="time-minutes">30</div>
            <div class="time-seconds">45</div>
        </div>
        <span class="auc-owner">
            <svg class="icon icon-facility">
                <use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#icon-facility"></use>
            </svg>
            <span class="field-content">Carson City Storage</span>
        </span>
        <div class="auc-address">Carson City, NV</div>
    </a>
</li>
"""

soup = BeautifulSoup(html, 'html.parser')
auction = soup.find('li', class_='auction-search-result')

# Test facility name parsing
owner_elem = auction.find('span', class_='auc-owner')
facility_name = 'Unknown Facility'
if owner_elem:
    field_content = owner_elem.find('span', class_='field-content')
    if field_content:
        facility_name = field_content.text.strip()

print("=" * 60)
print("Test 1: Facility Name Parsing")
print("=" * 60)
print(f"Found facility name: '{facility_name}'")
print(f"Expected: 'Carson City Storage'")
print(f"Match: {facility_name == 'Carson City Storage'}")
print()

# Test address parsing
address_elem = auction.find('div', class_='auc-address')
address = address_elem.text.strip() if address_elem else ''

print("=" * 60)
print("Test 2: Address Parsing")
print("=" * 60)
print(f"Found address element: {address_elem is not None}")
print(f"Address text: '{address}'")
print()

# Test city/state parsing
city = 'Unknown'
state = 'CA'
if address:
    parts = [p.strip() for p in address.split(',')]
    print(f"Split parts: {parts}")
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1][:2].upper()

print()
print("=" * 60)
print("Test 3: City/State Parsing")
print("=" * 60)
print(f"City: '{city}'")
print(f"State: '{state}'")
print(f"Expected: City='Carson City', State='NV'")
print(f"Match: {city == 'Carson City' and state == 'NV'}")
print()

# Now test with empty address (what might be happening)
html_no_address = """
<li class="auction-search-result">
    <a class="auction-link-wrapper" data-node-id="12345" href="/auction/12345">
        <span class="title">Unit A101</span>
        <div class="auc-address"></div>
    </a>
</li>
"""

soup2 = BeautifulSoup(html_no_address, 'html.parser')
auction2 = soup2.find('li', class_='auction-search-result')
address_elem2 = auction2.find('div', class_='auc-address')
address2 = address_elem2.text.strip() if address_elem2 else ''

print("=" * 60)
print("Test 4: Empty Address Element")
print("=" * 60)
print(f"Address element exists: {address_elem2 is not None}")
print(f"Address text: '{address2}'")
print(f"Address is empty: {not address2}")
print()

# Test with missing address element
html_missing_address = """
<li class="auction-search-result">
    <a class="auction-link-wrapper" data-node-id="12345" href="/auction/12345">
        <span class="title">Unit A101</span>
    </a>
</li>
"""

soup3 = BeautifulSoup(html_missing_address, 'html.parser')
auction3 = soup3.find('li', class_='auction-search-result')
address_elem3 = auction3.find('div', class_='auc-address')
address3 = address_elem3.text.strip() if address_elem3 else ''

print("=" * 60)
print("Test 5: Missing Address Element")
print("=" * 60)
print(f"Address element exists: {address_elem3 is not None}")
print(f"Address text: '{address3}'")
print(f"Would default to: city='Unknown', state='CA'")
print()

print("=" * 60)
print("Conclusion")
print("=" * 60)
print("If you're seeing 'Unknown, CA', it means:")
print("1. The div.auc-address element doesn't exist, OR")
print("2. The div.auc-address element exists but is empty")
print()
print("Possible solutions:")
print("1. Check the actual HTML structure of bid13.com")
print("2. Look for a different element that contains location")
print("3. Parse city/state from the search URL parameters")
