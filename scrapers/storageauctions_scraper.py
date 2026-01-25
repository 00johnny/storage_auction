"""
StorageAuctions.com Scraper

Scrapes storage auction data from storageauctions.com
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from typing import List, Dict
from .base_scraper import BaseScraper


class StorageAuctionsScraper(BaseScraper):
    """Scraper for storageauctions.com"""

    def __init__(self, provider_id: str, search_state: str = 'CA'):
        """
        Initialize StorageAuctions scraper

        Args:
            provider_id: UUID of the provider in database
            search_state: State abbreviation to search (default: CA)
        """
        super().__init__(provider_id)
        self.search_state = search_state
        self.base_url = f"https://www.storageauctions.com/auction-unit/find-auctions?AuctionsUnitsSearch[zip_city_state]={search_state}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all auctions, following pagination

        Returns:
            List of auction dictionaries
        """
        all_auctions = []
        current_url = self.base_url

        while current_url:
            try:
                page_auctions, next_url = self._scrape_page(current_url)
                all_auctions.extend(page_auctions)

                if next_url:
                    current_url = next_url
                    time.sleep(2)  # Delay to avoid rate-limiting
                else:
                    current_url = None

            except Exception as e:
                print(f"Error scraping page {current_url}: {e}")
                break

        return all_auctions

    def _scrape_page(self, url: str) -> tuple[List[Dict], str]:
        """
        Scrape a single page of auctions

        Args:
            url: URL to scrape

        Returns:
            Tuple of (auction list, next page URL or None)
        """
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract datetime mappings from JavaScript
        pattern = re.compile(
            r'moment\.tz\("([^"]+)",\s*"[^"]+"\);\s*setModel\("AuctionsUnits","(\d+)"\)',
            re.DOTALL
        )
        matching_dtms = pattern.findall(response.text)
        dtm_map = {id_: dt for dt, id_ in matching_dtms}

        # Find auction listings
        main_list = soup.find('ul', class_='main-list-wrap')
        if not main_list:
            return [], None

        auctions_html = main_list.find_all('li')

        auction_data_list = []
        for auction in auctions_html:
            if not auction.find('div'):
                continue

            try:
                auction_data = self._parse_auction(auction, dtm_map)
                if auction_data:
                    auction_data_list.append(auction_data)
            except Exception as e:
                print(f"Error parsing auction: {e}")
                continue

        # Find next page URL
        next_page = soup.find('a', class_='next-page')
        next_url = f"https://www.storageauctions.com{next_page['href']}" if next_page else None

        return auction_data_list, next_url

    def _parse_auction(self, auction, dtm_map: Dict) -> Dict:
        """
        Parse a single auction element

        Args:
            auction: BeautifulSoup element containing auction data
            dtm_map: Dictionary mapping auction IDs to datetime strings

        Returns:
            Dictionary with standardized auction data
        """
        # Extract facility/provider name
        facility_elem = auction.find('div', class_='location')
        facility = facility_elem.text.strip() if facility_elem else 'Unknown'

        # Extract address
        address_elem = auction.find('address')
        address = address_elem.text.strip() if address_elem else ''

        # Parse address into components (basic parsing)
        city = 'Unknown'
        state = self.search_state
        zip_code = '00000'
        if address:
            parts = address.split(',')
            if len(parts) >= 2:
                city = parts[-2].strip()
                state_zip = parts[-1].strip().split()
                if len(state_zip) >= 2:
                    state = state_zip[0]
                    zip_code = state_zip[1]

        # Extract unit size
        size_elem = auction.find('span', class_='auction-unit-size')
        unit_size = size_elem.text.strip() if size_elem else None

        # Extract current bid and ID
        current_bid_html = auction.find('span', {"id": re.compile('^current_bid_.*')})
        current_bid_text = current_bid_html.text.strip() if current_bid_html else '$0'
        current_bid = float(current_bid_text.replace('$', '').replace(',', '')) if '$' in current_bid_text else 0

        auction_id = None
        if current_bid_html:
            match = re.search(r'current_bid_(.*)', current_bid_html['id'])
            auction_id = match.group(1) if match else None

        # Get end time from dtm_map
        closes_at_str = dtm_map.get(auction_id)
        closes_at = None
        if closes_at_str:
            try:
                closes_at = datetime.fromisoformat(closes_at_str.replace('Z', '+00:00'))
            except:
                closes_at = None

        # Extract link
        link_elem = auction.find('img', class_='auctionTn')
        link = ''
        if link_elem and link_elem.get('onclick'):
            link_match = re.search(r'"(.*)"', link_elem.get('onclick'))
            if link_match:
                link = link_match.group(1)
                if link.startswith('/'):
                    link = f"https://www.storageauctions.com{link}"

        if not auction_id:
            return None

        return {
            'external_auction_id': auction_id,
            'unit_number': f"Unit-{auction_id}",  # No specific unit number provided
            'unit_size': unit_size,
            'description': f'Storage auction at {facility}',
            'facility_name': facility,
            'address_line1': address.split(',')[0] if address else '',
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'starts_at': datetime.now(),
            'closes_at': closes_at,
            'minimum_bid': current_bid,  # Assume current bid is minimum for now
            'current_bid': current_bid,
            'bid_increment': 25.00,
            'source_url': link
        }

    def scrape_updates(self, auction_ids: List[str]) -> List[Dict]:
        """
        Scrape updates for specific auctions
        For StorageAuctions.com, we scrape all and filter

        Args:
            auction_ids: List of external auction IDs to update

        Returns:
            List of updated auction dictionaries
        """
        all_auctions = self.scrape_all()
        return [a for a in all_auctions if a['external_auction_id'] in auction_ids]

    def run_scraper(self, full_scrape: bool = True, dry_run: bool = False) -> Dict:
        """
        Run the scraper and save to database

        Args:
            full_scrape: If True, scrape all auctions. If False, only update existing
            dry_run: If True, scrape but don't save to database (for testing)

        Returns:
            Dictionary with scraping results
        """
        print(f"Starting StorageAuctions.com scraper for provider {self.provider_id} (dry_run={dry_run})")

        try:
            if full_scrape:
                auctions = self.scrape_all()
            else:
                # Get list of existing auction IDs
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

            # If dry run, just return the data without saving
            if dry_run:
                # Check which would be added vs updated
                for auction_data in auctions:
                    if self.auction_exists(auction_data['external_auction_id']):
                        auctions_updated += 1
                    else:
                        auctions_added += 1

                return {
                    'status': 'success',
                    'dry_run': True,
                    'auctions_found': auctions_found,
                    'auctions_added': auctions_added,
                    'auctions_updated': auctions_updated,
                    'auctions': auctions  # Include actual auction data for preview
                }

            # Normal mode: save to database
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
