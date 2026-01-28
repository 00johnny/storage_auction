#!/usr/bin/env python3
"""
Import Pre-Geocoded California Cities

Quick solution: Import coordinates for common California cities
without needing internet access.

This uses california_cities_coords.json which contains pre-geocoded
coordinates for common Sacramento area cities.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def import_california_coords():
    """Import California city coordinates"""
    print("=" * 60)
    print("IMPORT CALIFORNIA CITY COORDINATES")
    print("=" * 60)

    # Read pre-geocoded California cities
    with open('california_cities_coords.json', 'r') as f:
        ca_cities = json.load(f)

    print(f"\nImporting {len(ca_cities)} California city coordinates...\n")

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    total_updated = 0

    for city_data in ca_cities:
        city = city_data['city']
        state = city_data['state']
        lat = city_data['latitude']
        lon = city_data['longitude']

        # Update auctions for this city
        cursor.execute("""
            UPDATE auctions
            SET latitude = %s,
                longitude = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE city = %s
              AND state = %s
              AND (latitude IS NULL OR longitude IS NULL)
        """, (lat, lon, city, state))

        updated = cursor.rowcount
        conn.commit()

        if updated > 0:
            print(f"✓ {city}, {state} → {lat:.6f}, {lon:.6f} ({updated} auctions)")
            total_updated += updated

        # Cache the coordinates
        try:
            cursor.execute("""
                INSERT INTO geocoded_locations (location_type, location_key, latitude, longitude, hit_count)
                VALUES ('city_state', %s, %s, %s, 0)
                ON CONFLICT (location_type, location_key) DO NOTHING
            """, (f"{city},{state}", lat, lon))
            conn.commit()
        except Exception:
            # Table might not exist
            pass

    # Check for remaining cities
    cursor.execute("""
        SELECT DISTINCT city, state, COUNT(*) as count
        FROM auctions
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND city IS NOT NULL
          AND state IS NOT NULL
        GROUP BY city, state
        ORDER BY count DESC
    """)

    remaining = cursor.fetchall()

    cursor.close()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total auctions updated: {total_updated}")

    if remaining:
        print(f"\nRemaining cities without coordinates: {len(remaining)}")
        print("\nCities still needing geocoding:")
        for city in remaining[:10]:  # Show first 10
            print(f"  - {city['city']}, {city['state']} ({city['count']} auctions)")
        if len(remaining) > 10:
            print(f"  ... and {len(remaining) - 10} more")

        print("\nTo geocode these:")
        print("1. Run: python export_locations.py")
        print("2. Copy locations_to_geocode.json to a machine with internet")
        print("3. Run: python geocode_offline.py")
        print("4. Copy geocoded_results.json back here")
        print("5. Run: python import_geocoded.py")
    else:
        print("\n✓ All auctions now have coordinates!")


if __name__ == '__main__':
    try:
        import_california_coords()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
