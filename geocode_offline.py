#!/usr/bin/env python3
"""
Geocode Locations Offline

Step 2: Run this on a machine WITH internet access

Reads locations_to_geocode.json and geocodes them using Nominatim.
Creates geocoded_results.json that can be imported on the server.
"""

import json
import requests
import time
import sys


def geocode_locations():
    """Geocode exported locations"""
    print("=" * 60)
    print("OFFLINE GEOCODING")
    print("=" * 60)

    # Read input file
    try:
        with open('locations_to_geocode.json', 'r') as f:
            locations = json.load(f)
    except FileNotFoundError:
        print("\n✗ Error: locations_to_geocode.json not found")
        print("\nMake sure you:")
        print("1. Ran export_locations.py on the server")
        print("2. Copied locations_to_geocode.json to this machine")
        sys.exit(1)

    print(f"\nGeocoding {len(locations)} locations...")
    print("This may take a while (1 second per location due to rate limiting)\n")

    results = []
    base_url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'StorageAuctionPlatform/1.0'}

    for i, loc in enumerate(locations, 1):
        city = loc['city']
        state = loc['state']
        zipcode = loc.get('zipcode')

        print(f"[{i}/{len(locations)}] {city}, {state}", end=" ")

        coords = None

        # Try zipcode first if available
        if zipcode:
            try:
                time.sleep(1.5)  # Rate limiting (1.5 seconds for safety)
                params = {
                    'postalcode': zipcode,
                    'country': 'United States',
                    'format': 'json',
                    'limit': 1
                }
                response = requests.get(base_url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data:
                    coords = (float(data[0]['lat']), float(data[0]['lon']))
                    print(f"(ZIP: {zipcode})", end=" ")
            except Exception as e:
                print(f"(ZIP failed)", end=" ")

        # Fallback to city/state
        if not coords:
            try:
                time.sleep(1.5)  # Rate limiting (1.5 seconds for safety)
                params = {
                    'city': city,
                    'state': state,
                    'country': 'United States',
                    'format': 'json',
                    'limit': 1
                }
                response = requests.get(base_url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data:
                    coords = (float(data[0]['lat']), float(data[0]['lon']))
                    print("(City/State)", end=" ")
            except Exception as e:
                print(f"✗ Failed: {e}")
                continue

        if coords:
            results.append({
                'city': city,
                'state': state,
                'zipcode': zipcode,
                'latitude': coords[0],
                'longitude': coords[1]
            })
            print(f"→ {coords[0]:.6f}, {coords[1]:.6f} ✓")
        else:
            print("✗ Could not geocode")

    # Write results
    output_file = 'geocoded_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n" + "=" * 60)
    print(f"✓ Geocoded {len(results)}/{len(locations)} locations")
    print(f"✓ Results saved to: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Copy '{output_file}' back to the server")
    print(f"2. Run: python import_geocoded.py")


if __name__ == '__main__':
    try:
        geocode_locations()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
