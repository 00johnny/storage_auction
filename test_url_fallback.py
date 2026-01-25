#!/usr/bin/env python3
"""
Test URL fallback parsing for city/state
"""
from urllib.parse import urlparse, parse_qs

# Test extracting from provider URL
facility_url = "https://bid13.com/property-search?city=Sacramento&state=CA"

print("=" * 60)
print("Test: Extracting city/state from URL")
print("=" * 60)
print(f"URL: {facility_url}")
print()

parsed_url = urlparse(facility_url)
params = parse_qs(parsed_url.query)

print(f"Query params: {params}")
print()

city = 'Unknown'
state = 'CA'

if 'city' in params and params['city']:
    city = params['city'][0]
    print(f"Extracted city: {city}")

if 'state' in params and params['state']:
    state = params['state'][0][:2].upper()
    print(f"Extracted state: {state}")

print()
print(f"Final result: {city}, {state}")
print(f"Expected: Sacramento, CA")
print(f"Match: {city == 'Sacramento' and state == 'CA'}")
