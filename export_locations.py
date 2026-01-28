#!/usr/bin/env python3
"""
Export Locations for Offline Geocoding

Step 1: Run this on the server to export locations that need geocoding
Step 2: Run geocode_offline.py on a machine with internet
Step 3: Run import_geocoded.py on the server to import results

This script exports unique city/state combinations from auctions.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def export_locations():
    """Export unique locations that need geocoding"""
    print("=" * 60)
    print("EXPORT LOCATIONS FOR OFFLINE GEOCODING")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Get unique city/state/zipcode combinations needing coordinates
    cursor.execute("""
        SELECT DISTINCT city, state, zip_code
        FROM auctions
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND city IS NOT NULL
          AND state IS NOT NULL
        ORDER BY state, city
    """)

    locations = cursor.fetchall()

    print(f"\nFound {len(locations)} unique locations needing geocoding\n")

    if len(locations) == 0:
        print("✓ All auctions already have coordinates!")
        cursor.close()
        conn.close()
        return

    # Convert to list of dicts
    export_data = []
    for loc in locations:
        export_data.append({
            'city': loc['city'],
            'state': loc['state'],
            'zipcode': loc['zip_code'] if loc['zip_code'] not in ['00000', '99999', None] else None
        })

    # Write to JSON file
    output_file = 'locations_to_geocode.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✓ Exported {len(export_data)} locations to: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Copy '{output_file}' to a machine with internet access")
    print(f"2. Run: python geocode_offline.py")
    print(f"3. Copy 'geocoded_results.json' back to this server")
    print(f"4. Run: python import_geocoded.py")

    # Also show unique city/state for manual lookup if needed
    print(f"\n" + "=" * 60)
    print("UNIQUE CITY/STATE COMBINATIONS:")
    print("=" * 60)

    cursor.execute("""
        SELECT DISTINCT city, state, COUNT(*) as auction_count
        FROM auctions
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND city IS NOT NULL
          AND state IS NOT NULL
        GROUP BY city, state
        ORDER BY state, city
    """)

    city_states = cursor.fetchall()
    for cs in city_states:
        print(f"{cs['city']}, {cs['state']} ({cs['auction_count']} auctions)")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    try:
        export_locations()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
