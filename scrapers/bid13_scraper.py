"""
Bid13.com Auction Scraper

Scrapes storage auction data from bid13.com
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class Bid13Scraper(BaseScraper):
    """Scraper for bid13.com auctions"""

    def __init__(self, provider_id: str, facility_url: str):
        """
        Initialize Bid13 scraper

        Args:
            provider_id: UUID of the provider in database
            facility_url: Full URL to the facility's auction page
        """
        super().__init__(provider_id)
        self.facility_url = facility_url
        self.base_url = 'https://bid13.com/'

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all auctions from the facility page

        Returns:
            List of auction dictionaries
        """
        try:
            response = requests.get(self.facility_url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        auctions = soup.find_all('li', {"class": 'auction-search-result'})

        auction_data_list = []
        for auction in auctions:
            try:
                auction_data = self._parse_auction(auction)
                if auction_data:
                    auction_data_list.append(auction_data)
            except Exception as e:
                print(f"Error parsing auction: {e}")
                continue

        return auction_data_list

    def _parse_auction(self, auction) -> Dict:
        """
        Parse a single auction element

        Args:
            auction: BeautifulSoup element containing auction data

        Returns:
            Dictionary with standardized auction data
        """
        node_link = auction.find('a', class_='auction-link-wrapper')
        if not node_link:
            return None

        external_id = node_link.get("data-node-id")
        url = node_link.get("href")
        unit = auction.find('span', class_='title')
        unit_text = unit.text.strip() if unit else 'N/A'

        size_elem = auction.find('span', class_='unit-size')
        size = size_elem.text.strip() if size_elem else None

        bid_elem = auction.find('div', class_='auc-current-bid')
        bid_text = bid_elem.text.strip() if bid_elem else '$0'
        # Extract numeric value from bid text (e.g., "$450" -> 450)
        bid = float(bid_text.replace('$', '').replace(',', '')) if '$' in bid_text else 0

        countdown_elem = auction.find('div', class_='countdown')
        end_time_str = countdown_elem.get("data-expiry") if countdown_elem else None

        # Parse end time (try multiple formats)
        closes_at = None
        if end_time_str:
            # Try different datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',           # 2026-01-25 15:30:00
                '%Y-%m-%dT%H:%M:%S',           # 2026-01-25T15:30:00
                '%Y-%m-%dT%H:%M:%SZ',          # 2026-01-25T15:30:00Z
                '%Y-%m-%d %H:%M:%S.%f',        # 2026-01-25 15:30:00.123456
            ]

            for fmt in formats:
                try:
                    closes_at = datetime.strptime(end_time_str.strip(), fmt)
                    break
                except ValueError:
                    continue

            # If all formats fail, try ISO format
            if not closes_at:
                try:
                    closes_at = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                except Exception as e:
                    print(f"Warning: Could not parse end time '{end_time_str}': {e}")

        # Skip auctions without end time - they're not useful
        if not closes_at:
            print(f"Skipping auction {external_id} - no valid end time (got: {end_time_str})")
            return None

        # Extract address if available
        address_elem = auction.find('div', class_='auc-address')
        address = address_elem.text.strip() if address_elem else ''

        return {
            'external_auction_id': external_id,
            'unit_number': unit_text,
            'unit_size': size,
            'description': f'Storage unit {unit_text}',
            'facility_name': 'Bid13 Facility',  # Can be extracted from page if available
            'address_line1': address,
            'city': 'Unknown',  # Parse from address if available
            'state': 'CA',
            'zip_code': '00000',  # Parse from address if available
            'starts_at': datetime.now(),
            'closes_at': closes_at,
            'minimum_bid': bid,  # First bid is minimum
            'current_bid': bid,
            'bid_increment': 25.00,
            'source_url': url if url.startswith('http') else f"{self.base_url}{url}"
        }

    def scrape_updates(self, auction_ids: List[str]) -> List[Dict]:
        """
        Scrape updates for specific auctions
        For Bid13, we scrape all and filter by auction_ids

        Args:
            auction_ids: List of external auction IDs to update

        Returns:
            List of updated auction dictionaries
        """
        all_auctions = self.scrape_all()
        return [a for a in all_auctions if a['external_auction_id'] in auction_ids]

    def run_scraper(self, full_scrape: bool = True) -> Dict:
        """
        Run the scraper and save to database

        Args:
            full_scrape: If True, scrape all auctions. If False, only update existing

        Returns:
            Dictionary with scraping results
        """
        print(f"Starting Bid13 scraper for provider {self.provider_id}")

        try:
            if full_scrape:
                auctions = self.scrape_all()
            else:
                # Get list of existing auction IDs for this provider
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT external_auction_id FROM auctions
                    WHERE provider_id = %s AND status = 'active'
                """, (self.provider_id,))
                auction_ids = [row['external_auction_id'] for row in cursor.fetchall()]
                cursor.close()
                conn.close()

                auctions = self.scrape_updates(auction_ids)

            auctions_found = len(auctions)
            auctions_added = 0
            auctions_updated = 0

            for auction_data in auctions:
                if self.auction_exists(auction_data['external_auction_id']):
                    self.save_auction(auction_data)
                    auctions_updated += 1
                else:
                    self.save_auction(auction_data)
                    auctions_added += 1

            # Log the scrape
            self.log_scrape('success', auctions_found, auctions_added, auctions_updated)

            print(f"Scraping complete: {auctions_found} found, {auctions_added} added, {auctions_updated} updated")

            return {
                'status': 'success',
                'auctions_found': auctions_found,
                'auctions_added': auctions_added,
                'auctions_updated': auctions_updated
            }

        except Exception as e:
            error_msg = str(e)
            print(f"Scraping failed: {error_msg}")
            self.log_scrape('failed', 0, 0, 0, error_msg)

            return {
                'status': 'failed',
                'error': error_msg
            }
