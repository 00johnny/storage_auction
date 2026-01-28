#!/usr/bin/env python3
"""
Fix Invalid ZIP Codes

Cleans up invalid ZIP codes in the auctions table.
Invalid codes like "00000", "99999", etc. prevent geocoding.

Usage:
    python fix_invalid_zipcodes.py           # Show invalid zipcodes
    python fix_invalid_zipcodes.py --fix     # Set invalid zipcodes to NULL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def fix_invalid_zipcodes(fix_mode: bool = False):
    """
    Find and optionally fix invalid ZIP codes

    Args:
        fix_mode: If True, set invalid zipcodes to NULL
    """
    print("=" * 60)
    print("INVALID ZIPCODE CHECKER")
    print("=" * 60)

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Find invalid zipcodes
    invalid_patterns = ['00000', '99999', 'N/A', 'Unknown', '']

    cursor.execute("""
        SELECT auction_id, facility_name, city, state, zip_code
        FROM auctions
        WHERE zip_code = ANY(%s) OR zip_code IS NULL OR LENGTH(TRIM(zip_code)) < 5
        ORDER BY city, state
    """, (invalid_patterns,))

    invalid_auctions = cursor.fetchall()

    print(f"\nFound {len(invalid_auctions)} auctions with invalid ZIP codes:\n")

    if len(invalid_auctions) == 0:
        print("✓ All ZIP codes are valid!")
        cursor.close()
        conn.close()
        return

    # Group by city/state
    by_location = {}
    for auction in invalid_auctions:
        location = f"{auction['city']}, {auction['state']}"
        if location not in by_location:
            by_location[location] = []
        by_location[location].append(auction)

    # Display grouped results
    for location, auctions in sorted(by_location.items()):
        print(f"\n{location}:")
        for auction in auctions:
            zip_display = auction['zip_code'] if auction['zip_code'] else 'NULL'
            facility = auction['facility_name'] or 'Unknown Facility'
            print(f"  - {facility}: ZIP={zip_display}")

    print("\n" + "=" * 60)

    if fix_mode:
        print("\n⚠️  FIXING INVALID ZIP CODES...")
        cursor.execute("""
            UPDATE auctions
            SET zip_code = NULL
            WHERE zip_code = ANY(%s) OR LENGTH(TRIM(zip_code)) < 5
        """, (invalid_patterns,))

        updated = cursor.rowcount
        conn.commit()

        print(f"✓ Set {updated} invalid ZIP codes to NULL")
        print("\nNote: Geocoding will now use city/state for these auctions")
    else:
        print("\n💡 To fix these, run: python fix_invalid_zipcodes.py --fix")
        print("\nThis will set invalid ZIP codes to NULL so geocoding")
        print("will fallback to city/state (which is more reliable)")

    cursor.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Find and fix invalid ZIP codes in auctions'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Set invalid ZIP codes to NULL (enables city/state geocoding)'
    )

    args = parser.parse_args()

    try:
        fix_invalid_zipcodes(fix_mode=args.fix)
    except psycopg2.OperationalError as e:
        print(f"\n✗ Database connection error: {e}")
        print("\nMake sure PostgreSQL is running and DATABASE_URL is set correctly.")
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
