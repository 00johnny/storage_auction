"""
Bid13.com Auction Scraper

Scrapes storage auction data from bid13.com
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

    def _parse_countdown_timer(self, countdown_elem) -> datetime:
        """
        Parse countdown timer from HTML elements

        Extracts days, hours, minutes, seconds from the countdown display
        and calculates the end time.

        Args:
            countdown_elem: BeautifulSoup element containing countdown timer

        Returns:
            datetime object for when auction closes, or None if parsing fails
        """
        try:
            days_elem = countdown_elem.find('div', class_='time-days')
            hours_elem = countdown_elem.find('div', class_='time-hours')
            minutes_elem = countdown_elem.find('div', class_='time-minutes')
            seconds_elem = countdown_elem.find('div', class_='time-seconds')

            # Helper function to safely parse int from text (handles empty strings)
            def safe_int(elem, default=0):
                if not elem:
                    return default
                text = elem.text.strip()
                if not text or text == '':
                    return default
                try:
                    return int(text)
                except ValueError:
                    return default

            days = safe_int(days_elem, 0)
            hours = safe_int(hours_elem, 0)
            minutes = safe_int(minutes_elem, 0)
            seconds = safe_int(seconds_elem, 0)

            # Calculate end time from now
            time_remaining = timedelta(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )

            closes_at = datetime.now() + time_remaining

            return closes_at

        except (ValueError, AttributeError) as e:
            print(f"Warning: Could not parse countdown timer: {e}")
            return None

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

        # Parse end time (try multiple methods)
        closes_at = None

        # Method 1: Try data-expiry attribute
        if end_time_str and end_time_str.strip():
            # Check if it's a Unix timestamp (all digits)
            if end_time_str.strip().isdigit():
                try:
                    closes_at = datetime.fromtimestamp(int(end_time_str))
                except (ValueError, OSError) as e:
                    print(f"Warning: Could not parse Unix timestamp '{end_time_str}': {e}")
            else:
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

        # Method 2: If data-expiry is empty, try countdown timer
        if not closes_at and countdown_elem:
            closes_at = self._parse_countdown_timer(countdown_elem)

        # Skip auctions without end time - they're not useful
        if not closes_at:
            print(f"Skipping auction {external_id} - no valid end time (data-expiry: '{end_time_str}', countdown: not found)")
            return None

        # Extract facility name from auc-owner span
        facility_name = 'Unknown Facility'
        owner_elem = auction.find('span', class_='auc-owner')
        if owner_elem:
            # Look for the field-content span inside auc-owner
            field_content = owner_elem.find('span', class_='field-content')
            if field_content:
                facility_name = field_content.text.strip()

        # Extract address if available
        address_elem = auction.find('div', class_='auc-address')
        address = address_elem.text.strip() if address_elem else ''

        # Parse city and state from address
        # Address format is typically: "City, State" or "City, ST"
        city = 'Unknown'
        state = 'CA'

        if address:
            # Try to parse "City, State" format
            parts = [p.strip() for p in address.split(',')]
            if len(parts) >= 2:
                city = parts[0]
                state = parts[1][:2].upper()  # Take first 2 chars and uppercase

        # Fallback: If address is empty, try to extract from facility_url query params
        if city == 'Unknown' and hasattr(self, 'facility_url'):
            from urllib.parse import urlparse, parse_qs
            try:
                parsed_url = urlparse(self.facility_url)
                params = parse_qs(parsed_url.query)

                # Debug once to see what's happening
                if not hasattr(self, '_url_debug_logged'):
                    print(f"URL fallback check - URL: {self.facility_url}")
                    print(f"URL params found: {params}")
                    self._url_debug_logged = True

                if 'city' in params and params['city']:
                    city = params['city'][0]

                if 'state' in params and params['state']:
                    state = params['state'][0][:2].upper()
            except Exception as e:
                print(f"Warning: Could not parse URL params for location: {e}")

        # Create or get facility record
        facility_data = {
            'facility_name': facility_name,
            'city': city,
            'state': state,
            'address_line1': address
        }
        facility_id = self.get_or_create_facility(facility_data)

        # Log summary for first auction only (to verify parsing is working)
        if not hasattr(self, '_first_auction_logged'):
            print(f"Sample auction parsed: Unit {unit_text} at {facility_name} in {city}, {state}")
            self._first_auction_logged = True

        return {
            'external_auction_id': external_id,
            'unit_number': unit_text,
            'unit_size': size,
            'description': f'Storage unit {unit_text}',
            'facility_id': facility_id,
            'facility_name': facility_name,
            'address_line1': address,
            'city': city,
            'state': state,
            'zip_code': '00000',  # Bid13 doesn't provide zip codes in listings
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

    def run_scraper(self, full_scrape: bool = True, dry_run: bool = False) -> Dict:
        """
        Run the scraper and save to database

        Args:
            full_scrape: If True, scrape all auctions. If False, only update existing
            dry_run: If True, scrape but don't save to database (for testing)

        Returns:
            Dictionary with scraping results
        """
        print(f"Starting Bid13 scraper for provider {self.provider_id} (dry_run={dry_run})")

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

            # Get unique facilities for summary
            unique_facilities = {}
            for auction in auctions:
                facility_key = f"{auction.get('facility_name')} ({auction.get('city')}, {auction.get('state')})"
                if facility_key not in unique_facilities:
                    unique_facilities[facility_key] = 0
                unique_facilities[facility_key] += 1

            # If dry run, just return the data without saving
            if dry_run:
                # Check which would be added vs updated
                for auction_data in auctions:
                    if self.auction_exists(auction_data['external_auction_id']):
                        auctions_updated += 1
                    else:
                        auctions_added += 1

                print(f"Dry run complete: {auctions_found} found, {auctions_added} would add, {auctions_updated} would update")
                print(f"Facilities found: {len(unique_facilities)}")
                for facility, count in sorted(unique_facilities.items()):
                    print(f"  - {facility}: {count} auctions")

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
            print(f"Facilities found: {len(unique_facilities)}")
            for facility, count in sorted(unique_facilities.items()):
                print(f"  - {facility}: {count} auctions")

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
