# Storage Auction Scrapers

This directory contains web scrapers for various storage auction platforms.

## Features

- **Database Integration**: All scrapers save directly to PostgreSQL
- **Duplicate Prevention**: Automatically checks `external_auction_id` to avoid duplicates
- **Update vs Full Scrape**: Support for both full scrapes and updating existing auctions
- **Scrape Logging**: All scraping activity is logged to `scrape_logs` table
- **Provider Management**: Each scraper is tied to a provider in the database

## Available Scrapers

### 1. Bid13Scraper
Scrapes auctions from bid13.com facilities.

```python
from scrapers import Bid13Scraper

# Create scraper instance
scraper = Bid13Scraper(
    provider_id='your-provider-uuid',
    facility_url='https://bid13.com/facilities/your-facility/address'
)

# Run full scrape
result = scraper.run_scraper(full_scrape=True)
print(f"Found: {result['auctions_found']}, Added: {result['auctions_added']}")

# Run update scrape (only existing auctions)
result = scraper.run_scraper(full_scrape=False)
```

### 2. StorageAuctionsScraper
Scrapes auctions from storageauctions.com by state.

```python
from scrapers import StorageAuctionsScraper

# Create scraper instance
scraper = StorageAuctionsScraper(
    provider_id='your-provider-uuid',
    search_state='CA'  # State abbreviation
)

# Run scraper
result = scraper.run_scraper(full_scrape=True)
```

## Provider CRUD API

### Create a Provider

```bash
curl -X POST http://ddev.us:5000/api/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bid13 - Leave It To Us Storage",
    "city": "Sacramento",
    "state": "CA",
    "zip_code": "95814",
    "website": "https://bid13.com",
    "source_url": "https://bid13.com/facilities/leave-it-us-storage/4395-business-drive",
    "scrape_frequency_hours": 6
  }'
```

### Get All Providers

```bash
curl http://ddev.us:5000/api/providers
```

### Get Single Provider

```bash
curl http://ddev.us:5000/api/providers/{provider_id}
```

### Update Provider

```bash
curl -X PUT http://ddev.us:5000/api/providers/{provider_id} \
  -H "Content-Type: application/json" \
  -d '{
    "scrape_frequency_hours": 12,
    "is_active": true
  }'
```

### Delete Provider (Soft Delete)

```bash
curl -X DELETE http://ddev.us:5000/api/providers/{provider_id}
```

### Trigger Manual Scrape

```bash
curl -X POST http://ddev.us:5000/api/providers/{provider_id}/scrape \
  -H "Content-Type: application/json" \
  -d '{"full_scrape": true}'
```

## Database Schema Mapping

The scrapers automatically map scraped data to the database schema:

| Scraper Field | Database Column | Notes |
|--------------|----------------|-------|
| external_auction_id | external_auction_id | Used for duplicate checking |
| unit_number | unit_number | Unit identifier |
| unit_size | unit_size | e.g., "10x10" |
| facility_name | facility_name | Storage facility name |
| address | address_line1 | Parsed from scraper |
| city | city | Parsed from address |
| state | state | Defaults to CA |
| zip_code | zip_code | Parsed from address |
| closes_at | closes_at | Auction end time |
| current_bid | current_bid | Current bid amount |
| source_url | source_url | Link to auction page |

## Creating a New Scraper

To add a scraper for a new auction platform:

1. Create a new file in `scrapers/` directory (e.g., `new_site_scraper.py`)
2. Extend the `BaseScraper` class
3. Implement required methods:
   - `scrape_all()`: Scrape all auctions from the site
   - `scrape_updates()`: Update specific auctions by ID
4. Add your scraper to `scrapers/__init__.py`

Example template:

```python
from .base_scraper import BaseScraper
from typing import List, Dict

class NewSiteScraper(BaseScraper):
    def __init__(self, provider_id: str, site_url: str):
        super().__init__(provider_id)
        self.site_url = site_url

    def scrape_all(self) -> List[Dict]:
        # Implement scraping logic
        # Return list of auction dictionaries
        pass

    def scrape_updates(self, auction_ids: List[str]) -> List[Dict]:
        # Implement update logic
        pass
```

## Scraping Frequency

The `scrape_frequency_hours` field in the providers table determines how often each provider should be scraped. You can:

1. Set it when creating a provider (default: 24 hours)
2. Update it via the API
3. Use it in a cron job or scheduler to automatically run scrapers

Example cron setup (run every hour, check which providers need scraping):

```python
# scheduler.py
import psycopg2
from datetime import datetime, timedelta
from scrapers import Bid13Scraper, StorageAuctionsScraper

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Find providers that need scraping
cursor.execute("""
    SELECT provider_id, source_url, scrape_frequency_hours
    FROM providers
    WHERE is_active = TRUE
    AND (
        last_scraped_at IS NULL
        OR last_scraped_at < NOW() - (scrape_frequency_hours || ' hours')::INTERVAL
    )
""")

providers = cursor.fetchall()

for provider in providers:
    # Determine scraper type and run
    if 'bid13.com' in provider['source_url']:
        scraper = Bid13Scraper(provider['provider_id'], provider['source_url'])
        scraper.run_scraper()
```

## Error Handling

All scrapers log their activity to the `scrape_logs` table:

- `status`: 'success', 'failed', or 'partial'
- `auctions_found`: Number of auctions discovered
- `auctions_added`: Number of new auctions added
- `auctions_updated`: Number of existing auctions updated
- `error_message`: Error details if scraping failed

Query recent scrape logs:

```sql
SELECT * FROM scrape_logs
WHERE provider_id = 'your-provider-id'
ORDER BY scrape_started_at DESC
LIMIT 10;
```

## Dependencies

Install required packages:

```bash
pip install requests beautifulsoup4 psycopg2-binary python-dotenv
```
