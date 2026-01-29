#!/usr/bin/env python3
"""
Backfill Missing/Invalid ZIP Codes

Finds the correct ZIP codes for auctions by geocoding city/state.
This fixes invalid zipcodes (00000, 99999) by looking them up.

Usage:
    python backfill_zipcodes.py              # Show what would be fixed
    python backfill_zipcodes.py --fix        # Actually update the database
    python backfill_zipcodes.py --limit 10   # Process only 10 cities
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import argparse
import requests
import time
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def backfill_zipcodes(fix_mode: bool = False, limit: int = None):
    """
    Find and fix invalid ZIP codes by geocoding city/state

    Args:
        fix_mode: If True, update the database
        limit: Max number of cities to process
    """
    print("=" * 60)
    print("BACKFILL INVALID ZIP CODES")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Find unique city/state combinations with invalid zipcodes
    invalid_patterns = ['00000', '99999', 'N/A', 'Unknown', '']

    query = """
        SELECT DISTINCT city, state, zip_code, COUNT(*) as auction_count
        FROM auctions
        WHERE (zip_code = ANY(%s) OR zip_code = '' OR LENGTH(TRIM(zip_code)) < 5)
          AND city IS NOT NULL
          AND state IS NOT NULL
        GROUP BY city, state, zip_code
        ORDER BY state, city
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, (invalid_patterns,))
    cities = cursor.fetchall()

    print(f"\nFound {len(cities)} city/state combinations with invalid ZIP codes\n")

    if len(cities) == 0:
        print("✓ All ZIP codes are valid!")
        cursor.close()
        conn.close()
        return

    if not fix_mode:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Geocode each city to find correct zipcode
    stats = {'success': 0, 'failed': 0, 'total_auctions': 0}

    for i, city_data in enumerate(cities, 1):
        city = city_data['city']
        state = city_data['state']
        old_zip = city_data['zip_code'] or 'empty'
        auction_count = city_data['auction_count']

        print(f"[{i}/{len(cities)}] {city}, {state} (current: {old_zip}, {auction_count} auctions)", end=" ")

        try:
            # Rate limiting
            time.sleep(1.5)

            # Geocode city/state
            params = {
                'city': city,
                'state': state,
                'country': 'United States',
                'format': 'json',
                'addressdetails': 1,  # Request full address details
                'limit': 1
            }

            response = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params=params,
                headers={'User-Agent': 'StorageAuctionPlatform/1.0'},
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if results and len(results) > 0:
                result = results[0]
                address = result.get('address', {})

                # Try to extract zipcode from various fields
                new_zip = (
                    address.get('postcode') or
                    address.get('postal_code') or
                    address.get('zipcode')
                )

                if new_zip:
                    # Clean up zipcode (might have extra info like "95814-2103")
                    new_zip = new_zip.split('-')[0].strip()

                    if len(new_zip) == 5 and new_zip.isdigit():
                        print(f"→ Found ZIP: {new_zip}", end=" ")

                        if fix_mode:
                            # Update all auctions in this city/state with invalid zip
                            cursor.execute("""
                                UPDATE auctions
                                SET zip_code = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE city = %s
                                  AND state = %s
                                  AND (zip_code = ANY(%s) OR zip_code = '' OR LENGTH(TRIM(zip_code)) < 5)
                            """, (new_zip, city, state, invalid_patterns))

                            updated = cursor.rowcount
                            conn.commit()

                            print(f"✓ Updated {updated} auctions")
                            stats['total_auctions'] += updated
                        else:
                            print("✓ (dry-run)")

                        stats['success'] += 1
                    else:
                        print(f"✗ Invalid format: {new_zip}")
                        stats['failed'] += 1
                else:
                    print("✗ No zipcode in geocoding result")
                    stats['failed'] += 1
            else:
                print("✗ Geocoding returned no results")
                stats['failed'] += 1

        except requests.exceptions.RequestException as e:
            if "429" in str(e):
                print("✗ Rate limited - try again later")
                print("\n⚠️  Hit rate limit. Wait a few minutes and try again.")
                break
            else:
                print(f"✗ Request error: {e}")
                stats['failed'] += 1
        except Exception as e:
            print(f"✗ Error: {e}")
            stats['failed'] += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Cities successfully processed: {stats['success']}")
    print(f"Cities failed:                 {stats['failed']}")

    if fix_mode:
        print(f"Total auctions updated:        {stats['total_auctions']}")
        print("\n✓ Database updated!")
    else:
        print(f"\n[DRY RUN - No changes made]")
        print("\nTo apply these changes, run:")
        print("  python backfill_zipcodes.py --fix")

    cursor.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Backfill invalid ZIP codes by geocoding city/state'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Actually update the database (default is dry-run)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of cities to process'
    )

    args = parser.parse_args()

    try:
        backfill_zipcodes(fix_mode=args.fix, limit=args.limit)
    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
