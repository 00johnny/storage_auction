#!/usr/bin/env python3
"""
Debug Geocoding Results

Shows the full JSON response from Nominatim to see what data is available.
Helps debug why zipcodes aren't being found.

Usage:
    python debug_geocoding.py "Cameron Park" CA
    python debug_geocoding.py Sacramento CA
    python debug_geocoding.py "Cathedral city" CA
"""

import requests
import json
import sys


def debug_geocode(city, state):
    """Show full geocoding response"""
    print("=" * 60)
    print(f"DEBUG GEOCODING: {city}, {state}")
    print("=" * 60)

    # Test with addressdetails
    params = {
        'city': city,
        'state': state,
        'country': 'United States',
        'format': 'json',
        'addressdetails': 1,
        'limit': 3
    }

    url = "https://nominatim.openstreetmap.org/search"
    print(f"\nURL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}\n")

    try:
        response = requests.get(
            url,
            params=params,
            headers={'User-Agent': 'StorageAuctionPlatform/1.0'},
            timeout=10
        )
        response.raise_for_status()

        results = response.json()

        print(f"Found {len(results)} result(s)\n")
        print("=" * 60)

        for i, result in enumerate(results, 1):
            print(f"\nRESULT {i}:")
            print(json.dumps(result, indent=2))

            # Highlight important fields
            print("\n--- KEY FIELDS ---")
            print(f"Display Name: {result.get('display_name')}")
            print(f"Type: {result.get('type')}")
            print(f"Class: {result.get('class')}")
            print(f"Lat/Lon: {result.get('lat')}, {result.get('lon')}")

            if 'address' in result:
                print("\n--- ADDRESS DETAILS ---")
                address = result['address']
                print(json.dumps(address, indent=2))

                # Try to find zipcode in various fields
                print("\n--- ZIPCODE SEARCH ---")
                zipcode_fields = ['postcode', 'postal_code', 'zipcode', 'zip', 'postalCode']
                for field in zipcode_fields:
                    if field in address:
                        print(f"✓ Found in '{field}': {address[field]}")

                if not any(field in address for field in zipcode_fields):
                    print("✗ No zipcode found in any standard field")
                    print("Available address fields:", list(address.keys()))

            print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) < 3:
        print("Usage: python debug_geocoding.py <city> <state>")
        print("\nExamples:")
        print('  python debug_geocoding.py "Cameron Park" CA')
        print('  python debug_geocoding.py Sacramento CA')
        print('  python debug_geocoding.py "Cathedral city" CA')
        sys.exit(1)

    city = sys.argv[1]
    state = sys.argv[2]

    debug_geocode(city, state)


if __name__ == '__main__':
    main()
