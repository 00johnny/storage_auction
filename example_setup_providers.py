"""
Example Script: Setting up Providers and Running Scrapers

This script demonstrates how to:
1. Create providers via the API
2. Run scrapers for those providers
3. Check scraping results

Run this after starting your Flask API server.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000"  # Change to your API URL

def create_provider(provider_data):
    """Create a new provider via API"""
    response = requests.post(
        f"{API_BASE_URL}/api/providers",
        json=provider_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 201:
        result = response.json()
        print(f"✓ Created provider: {provider_data['name']}")
        print(f"  Provider ID: {result['provider_id']}")
        return result['provider_id']
    else:
        print(f"✗ Failed to create provider: {response.json()}")
        return None

def trigger_scrape(provider_id, full_scrape=True):
    """Trigger a scrape for a provider"""
    response = requests.post(
        f"{API_BASE_URL}/api/providers/{provider_id}/scrape",
        json={'full_scrape': full_scrape},
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        scrape_result = result.get('scrape_result', {})
        print(f"✓ Scrape completed for provider {provider_id}")
        print(f"  Found: {scrape_result.get('auctions_found', 0)}")
        print(f"  Added: {scrape_result.get('auctions_added', 0)}")
        print(f"  Updated: {scrape_result.get('auctions_updated', 0)}")
        return scrape_result
    else:
        print(f"✗ Scrape failed: {response.json()}")
        return None

def get_providers():
    """Get all providers"""
    response = requests.get(f"{API_BASE_URL}/api/providers")

    if response.status_code == 200:
        result = response.json()
        providers = result.get('providers', [])
        print(f"✓ Found {len(providers)} providers")
        for p in providers:
            print(f"  - {p['name']} ({p['active_auctions']} active auctions)")
        return providers
    else:
        print(f"✗ Failed to get providers: {response.json()}")
        return []

def main():
    print("=" * 60)
    print("Storage Auction Platform - Provider Setup")
    print("=" * 60)
    print()

    # Example 1: Create a Bid13 provider
    print("Step 1: Creating Bid13 Provider...")
    bid13_provider = {
        "name": "Bid13 - Leave It To Us Storage",
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95814",
        "website": "https://bid13.com",
        "address_line1": "4395 Business Drive",
        "source_url": "https://bid13.com/facilities/leave-it-us-storage/4395-business-drive",
        "scrape_frequency_hours": 6,
        "is_active": True
    }

    bid13_id = create_provider(bid13_provider)
    print()

    # Example 2: Create a StorageAuctions.com "provider"
    # Note: StorageAuctions.com is an aggregator, so you might create a generic provider
    print("Step 2: Creating StorageAuctions.com Provider...")
    sa_provider = {
        "name": "StorageAuctions.com - California",
        "city": "Various",
        "state": "CA",
        "zip_code": "00000",
        "website": "https://www.storageauctions.com",
        "source_url": "https://www.storageauctions.com",  # Base URL
        "scrape_frequency_hours": 12,
        "is_active": True
    }

    sa_id = create_provider(sa_provider)
    print()

    # Wait a moment for database to settle
    time.sleep(1)

    # Example 3: Trigger scrapes
    if bid13_id:
        print("Step 3: Running Bid13 Scraper...")
        trigger_scrape(bid13_id, full_scrape=True)
        print()

    if sa_id:
        print("Step 4: Running StorageAuctions.com Scraper...")
        print("NOTE: This may take several minutes as it scrapes multiple pages...")
        trigger_scrape(sa_id, full_scrape=True)
        print()

    # Example 4: List all providers and their auction counts
    print("Step 5: Listing All Providers...")
    get_providers()
    print()

    print("=" * 60)
    print("Setup Complete!")
    print()
    print("Next steps:")
    print("1. Visit http://localhost:5000/ to see the frontend")
    print("2. Check http://localhost:5000/api/auctions for auction data")
    print("3. Set up a cron job to run scrapers periodically")
    print("=" * 60)

if __name__ == "__main__":
    main()
