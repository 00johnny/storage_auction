#!/usr/bin/env python3
"""
Backfill Auction Coordinates

Geocodes existing auctions that don't have lat/lon coordinates.
Uses the database-cached geocoding system for efficiency.

Usage:
    python backfill_auction_coordinates.py
    python backfill_auction_coordinates.py --limit 100  # Process only 100 auctions
    python backfill_auction_coordinates.py --dry-run    # Show what would be done
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
import argparse
from dotenv import load_dotenv
from geocoding_helper import SimpleGeocoder

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def backfill_coordinates(limit: int = None, dry_run: bool = False):
    """
    Backfill missing coordinates for auctions

    Args:
        limit: Maximum number of auctions to process (None = all)
        dry_run: If True, show what would be done without making changes
    """
    print("=" * 60)
    print("AUCTION COORDINATES BACKFILL")
    print("=" * 60)

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Count auctions needing geocoding
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM auctions
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND city IS NOT NULL
          AND state IS NOT NULL
    """)
    total_count = cursor.fetchone()['count']

    print(f"\nFound {total_count} auctions without coordinates")

    if total_count == 0:
        print("✓ All auctions already have coordinates!")
        cursor.close()
        conn.close()
        return

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    # Get auctions needing geocoding
    query = """
        SELECT auction_id, city, state, zip_code, facility_name
        FROM auctions
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND city IS NOT NULL
          AND state IS NOT NULL
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    auctions = cursor.fetchall()

    print(f"Processing {len(auctions)} auctions...\n")

    # Initialize geocoder with database connection
    geocoder = SimpleGeocoder(db_connection=conn)

    # Track statistics
    stats = {
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'from_cache': 0
    }

    # Process each auction
    for i, auction in enumerate(auctions, 1):
        auction_id = auction['auction_id']
        city = auction['city']
        state = auction['state']
        zip_code = auction['zip_code']
        facility_name = auction['facility_name'] or 'Unknown'

        print(f"[{i}/{len(auctions)}] {facility_name} - {city}, {state}", end=" ")

        try:
            # Try geocoding by ZIP code first, fallback to city/state
            coords = None

            if zip_code:
                coords = geocoder.geocode_zipcode(zip_code)
                if coords:
                    print(f"(ZIP: {zip_code})", end=" ")

            if not coords:
                coords = geocoder.geocode_city_state(city, state)
                if coords:
                    print(f"(City/State)", end=" ")

            if coords:
                lat, lon = coords

                if not dry_run:
                    # Update auction with coordinates
                    cursor.execute("""
                        UPDATE auctions
                        SET latitude = %s,
                            longitude = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE auction_id = %s
                    """, (lat, lon, auction_id))
                    conn.commit()

                print(f"→ {lat:.6f}, {lon:.6f} ✓")
                stats['success'] += 1
            else:
                print("→ Could not geocode ✗")
                stats['failed'] += 1

        except Exception as e:
            print(f"→ Error: {e} ✗")
            stats['failed'] += 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Successfully geocoded: {stats['success']}")
    print(f"Failed to geocode:     {stats['failed']}")
    print(f"Remaining:             {total_count - len(auctions)}")

    if dry_run:
        print("\n[DRY RUN - No changes were made]")
    else:
        print(f"\n✓ Database updated!")

    # Show cache statistics
    cursor.execute("SELECT COUNT(*) as count, SUM(hit_count) as total_hits FROM geocoded_locations")
    cache_stats = cursor.fetchone()
    if cache_stats and cache_stats['count']:
        print(f"\nGeocoding Cache: {cache_stats['count']} locations cached, {cache_stats['total_hits']} total hits")

    cursor.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Backfill geocoded coordinates for auctions'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of auctions to process'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    try:
        backfill_coordinates(limit=args.limit, dry_run=args.dry_run)
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
