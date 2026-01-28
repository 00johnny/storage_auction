#!/usr/bin/env python3
"""
Import Geocoded Results

Step 3: Run this on the server to import geocoded coordinates

Reads geocoded_results.json and updates the database.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def import_geocoded():
    """Import geocoded coordinates into database"""
    print("=" * 60)
    print("IMPORT GEOCODED RESULTS")
    print("=" * 60)

    # Read results file
    try:
        with open('geocoded_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("\n✗ Error: geocoded_results.json not found")
        print("\nMake sure you:")
        print("1. Ran geocode_offline.py on a machine with internet")
        print("2. Copied geocoded_results.json to this server")
        sys.exit(1)

    print(f"\nImporting {len(results)} geocoded locations...\n")

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    stats = {'updated': 0, 'cached': 0, 'failed': 0}

    for i, result in enumerate(results, 1):
        city = result['city']
        state = result['state']
        zipcode = result.get('zipcode')
        lat = result['latitude']
        lon = result['longitude']

        print(f"[{i}/{len(results)}] {city}, {state} → {lat:.6f}, {lon:.6f}", end=" ")

        try:
            # Update all auctions for this city/state
            if zipcode:
                cursor.execute("""
                    UPDATE auctions
                    SET latitude = %s,
                        longitude = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE city = %s
                      AND state = %s
                      AND zip_code = %s
                      AND (latitude IS NULL OR longitude IS NULL)
                """, (lat, lon, city, state, zipcode))
            else:
                cursor.execute("""
                    UPDATE auctions
                    SET latitude = %s,
                        longitude = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE city = %s
                      AND state = %s
                      AND (latitude IS NULL OR longitude IS NULL)
                """, (lat, lon, city, state))

            updated_count = cursor.rowcount
            conn.commit()

            # Also cache in geocoded_locations table if it exists
            try:
                # Try to insert into cache
                if zipcode:
                    cursor.execute("""
                        INSERT INTO geocoded_locations (location_type, location_key, latitude, longitude, hit_count)
                        VALUES ('zipcode', %s, %s, %s, 0)
                        ON CONFLICT (location_type, location_key) DO NOTHING
                    """, (zipcode, lat, lon))

                cursor.execute("""
                    INSERT INTO geocoded_locations (location_type, location_key, latitude, longitude, hit_count)
                    VALUES ('city_state', %s, %s, %s, 0)
                    ON CONFLICT (location_type, location_key) DO NOTHING
                """, (f"{city},{state}", lat, lon))

                conn.commit()
                stats['cached'] += 1
            except Exception:
                # Table might not exist, that's okay
                pass

            print(f"✓ ({updated_count} auctions)")
            stats['updated'] += updated_count

        except Exception as e:
            print(f"✗ Error: {e}")
            stats['failed'] += 1

    cursor.close()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Auctions updated:      {stats['updated']}")
    print(f"Locations cached:      {stats['cached']}")
    print(f"Failed:                {stats['failed']}")
    print(f"\n✓ Import complete!")


if __name__ == '__main__':
    try:
        import_geocoded()
    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
