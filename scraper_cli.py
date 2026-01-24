#!/usr/bin/env python3
"""
Storage Auction Scraper CLI

Command-line interface for running scrapers manually or in cron jobs.

Usage:
    python scraper_cli.py list-providers
    python scraper_cli.py run --provider-id <uuid>
    python scraper_cli.py run --all
    python scraper_cli.py run --all --update-only
    python scraper_cli.py run --provider-name "Bid13"
    python scraper_cli.py test --provider-id <uuid>
"""

import argparse
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path to import scrapers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import Bid13Scraper, StorageAuctionsScraper

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def list_providers():
    """List all providers"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.provider_id,
            p.name,
            p.city,
            p.state,
            p.is_active,
            p.scrape_frequency_hours,
            p.last_scraped_at,
            COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.auction_id END) as active_auctions
        FROM providers p
        LEFT JOIN auctions a ON p.provider_id = a.provider_id
        GROUP BY p.provider_id
        ORDER BY p.name
    """)

    providers = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\n{'ID':<38} {'Name':<40} {'Location':<20} {'Active':<8} {'Freq(h)':<8} {'Auctions':<10} {'Last Scraped'}")
    print("=" * 160)

    for p in providers:
        last_scraped = p['last_scraped_at'].strftime('%Y-%m-%d %H:%M') if p['last_scraped_at'] else 'Never'
        active = '✓' if p['is_active'] else '✗'
        print(f"{p['provider_id']:<38} {p['name']:<40} {p['city']}, {p['state']:<17} {active:<8} {p['scrape_frequency_hours']:<8} {p['active_auctions']:<10} {last_scraped}")

    print(f"\nTotal: {len(providers)} providers\n")
    return providers


def get_scraper_for_provider(provider_id):
    """
    Get the appropriate scraper instance for a provider

    Args:
        provider_id: Provider UUID

    Returns:
        Scraper instance or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provider_id, name, source_url
        FROM providers
        WHERE provider_id = %s AND is_active = TRUE
    """, (provider_id,))

    provider = cursor.fetchone()
    cursor.close()
    conn.close()

    if not provider:
        print(f"Error: Provider {provider_id} not found or inactive")
        return None

    source_url = provider['source_url']

    if not source_url:
        print(f"Error: Provider '{provider['name']}' has no source_url configured")
        return None

    # Determine scraper type based on URL
    if 'bid13.com' in source_url:
        return Bid13Scraper(provider_id, source_url)
    elif 'storageauctions.com' in source_url:
        return StorageAuctionsScraper(provider_id)
    else:
        print(f"Error: No scraper available for URL: {source_url}")
        return None


def run_scraper(provider_id, full_scrape=True, dry_run=False):
    """
    Run scraper for a specific provider

    Args:
        provider_id: Provider UUID
        full_scrape: If True, scrape all auctions. If False, only update existing
        dry_run: If True, don't save to database
    """
    print(f"\n{'='*60}")
    print(f"Running scraper for provider: {provider_id}")
    print(f"Mode: {'Full Scrape' if full_scrape else 'Update Only'}")
    print(f"Dry Run: {'Yes' if dry_run else 'No'}")
    print(f"{'='*60}\n")

    scraper = get_scraper_for_provider(provider_id)
    if not scraper:
        return False

    try:
        if dry_run:
            # Just scrape without saving
            auctions = scraper.scrape_all() if full_scrape else []
            print(f"\nDry run complete:")
            print(f"  Would have found: {len(auctions)} auctions")
            if auctions:
                print(f"\nSample auction:")
                print(f"  Unit: {auctions[0].get('unit_number')}")
                print(f"  Size: {auctions[0].get('unit_size')}")
                print(f"  Bid: ${auctions[0].get('current_bid')}")
                print(f"  Closes: {auctions[0].get('closes_at')}")
            return True
        else:
            # Run scraper and save to database
            result = scraper.run_scraper(full_scrape=full_scrape)

            if result['status'] == 'success':
                print(f"\n✓ Scrape completed successfully!")
                print(f"  Found: {result['auctions_found']}")
                print(f"  Added: {result['auctions_added']}")
                print(f"  Updated: {result['auctions_updated']}")
                return True
            else:
                print(f"\n✗ Scrape failed: {result.get('error')}")
                return False

    except Exception as e:
        print(f"\n✗ Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_scrapers(full_scrape=True, check_frequency=False):
    """
    Run scrapers for all active providers

    Args:
        full_scrape: If True, scrape all auctions. If False, only update existing
        check_frequency: If True, only scrape providers that are due based on scrape_frequency_hours
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT provider_id, name, scrape_frequency_hours, last_scraped_at
        FROM providers
        WHERE is_active = TRUE AND source_url IS NOT NULL
    """

    if check_frequency:
        query += """
            AND (
                last_scraped_at IS NULL
                OR last_scraped_at < NOW() - (scrape_frequency_hours || ' hours')::INTERVAL
            )
        """

    cursor.execute(query)
    providers = cursor.fetchall()
    cursor.close()
    conn.close()

    if not providers:
        print("\nNo providers to scrape.")
        return

    print(f"\n{'='*60}")
    print(f"Running scrapers for {len(providers)} provider(s)")
    print(f"{'='*60}\n")

    success_count = 0
    fail_count = 0

    for provider in providers:
        print(f"\nProvider: {provider['name']}")
        success = run_scraper(provider['provider_id'], full_scrape=full_scrape)

        if success:
            success_count += 1
        else:
            fail_count += 1

        print(f"{'-'*60}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"{'='*60}\n")


def find_provider_by_name(name):
    """Find provider by name (partial match)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT provider_id, name
        FROM providers
        WHERE is_active = TRUE AND name ILIKE %s
    """, (f"%{name}%",))

    providers = cursor.fetchall()
    cursor.close()
    conn.close()

    if not providers:
        print(f"No active providers found matching '{name}'")
        return None
    elif len(providers) > 1:
        print(f"\nMultiple providers found matching '{name}':")
        for p in providers:
            print(f"  - {p['name']} ({p['provider_id']})")
        print("\nPlease use --provider-id with the specific UUID")
        return None
    else:
        return providers[0]['provider_id']


def main():
    parser = argparse.ArgumentParser(
        description='Storage Auction Scraper CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all providers
  %(prog)s list-providers

  # Run scraper for specific provider
  %(prog)s run --provider-id abc123-def456-...

  # Run scraper by provider name
  %(prog)s run --provider-name "Bid13"

  # Run all scrapers
  %(prog)s run --all

  # Run only providers that are due (based on scrape_frequency_hours)
  %(prog)s run --all --check-frequency

  # Update only (don't scrape new auctions)
  %(prog)s run --all --update-only

  # Dry run (don't save to database)
  %(prog)s run --provider-id abc123 --dry-run
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List providers command
    subparsers.add_parser('list-providers', help='List all providers')

    # Run scraper command
    run_parser = subparsers.add_parser('run', help='Run scraper(s)')
    run_parser.add_argument('--provider-id', help='Provider UUID to scrape')
    run_parser.add_argument('--provider-name', help='Provider name to scrape (partial match)')
    run_parser.add_argument('--all', action='store_true', help='Run all active scrapers')
    run_parser.add_argument('--update-only', action='store_true', help='Only update existing auctions (no new scrapes)')
    run_parser.add_argument('--check-frequency', action='store_true', help='Only scrape providers that are due')
    run_parser.add_argument('--dry-run', action='store_true', help='Test scraper without saving to database')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'list-providers':
        list_providers()

    elif args.command == 'run':
        full_scrape = not args.update_only

        if args.all:
            run_all_scrapers(full_scrape=full_scrape, check_frequency=args.check_frequency)
        elif args.provider_id:
            run_scraper(args.provider_id, full_scrape=full_scrape, dry_run=args.dry_run)
        elif args.provider_name:
            provider_id = find_provider_by_name(args.provider_name)
            if provider_id:
                run_scraper(provider_id, full_scrape=full_scrape, dry_run=args.dry_run)
        else:
            print("Error: Must specify --provider-id, --provider-name, or --all")
            run_parser.print_help()
            sys.exit(1)


if __name__ == '__main__':
    main()
