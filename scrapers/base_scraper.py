"""
Storage Auction Scraper Base Class

Provides common functionality for all auction site scrapers including:
- Database integration
- Duplicate checking
- Provider management
- Standardized data format
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class BaseScraper:
    """Base class for all auction scrapers"""

    def __init__(self, provider_id: str):
        """
        Initialize scraper with provider ID

        Args:
            provider_id: UUID of the provider in the database
        """
        self.provider_id = provider_id
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')

    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def auction_exists(self, external_auction_id: str) -> bool:
        """
        Check if auction already exists in database

        Args:
            external_auction_id: The auction ID from the external site

        Returns:
            True if auction exists, False otherwise
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT auction_id FROM auctions
            WHERE external_auction_id = %s AND provider_id = %s
        """, (external_auction_id, self.provider_id))

        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()

        return exists

    def save_auction(self, auction_data: Dict) -> Optional[str]:
        """
        Save or update auction in database

        Args:
            auction_data: Dictionary containing auction information

        Returns:
            auction_id if successful, None otherwise
        """
        # Validate required fields
        if not auction_data.get('closes_at'):
            print(f"Warning: Skipping auction {auction_data.get('external_auction_id')} - missing required field: closes_at")
            return None

        if not auction_data.get('external_auction_id'):
            print(f"Warning: Skipping auction - missing external_auction_id")
            return None

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if auction exists
            cursor.execute("""
                SELECT auction_id FROM auctions
                WHERE external_auction_id = %s AND provider_id = %s
            """, (auction_data.get('external_auction_id'), self.provider_id))

            existing = cursor.fetchone()

            if existing:
                # Update existing auction
                auction_id = existing['auction_id']
                cursor.execute("""
                    UPDATE auctions SET
                        unit_number = %s,
                        unit_size = %s,
                        description = %s,
                        city = %s,
                        state = %s,
                        zip_code = %s,
                        closes_at = %s,
                        current_bid = %s,
                        minimum_bid = %s,
                        source_url = %s,
                        last_scraped_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE auction_id = %s
                """, (
                    auction_data.get('unit_number', 'N/A'),
                    auction_data.get('unit_size'),
                    auction_data.get('description', ''),
                    auction_data.get('city', 'Unknown'),
                    auction_data.get('state', 'CA'),
                    auction_data.get('zip_code', '00000'),
                    auction_data.get('closes_at'),
                    auction_data.get('current_bid', 0),
                    auction_data.get('minimum_bid', 0),
                    auction_data.get('source_url'),
                    auction_id
                ))
            else:
                # Insert new auction
                cursor.execute("""
                    INSERT INTO auctions (
                        provider_id,
                        unit_number,
                        unit_size,
                        description,
                        facility_name,
                        address_line1,
                        city,
                        state,
                        zip_code,
                        starts_at,
                        closes_at,
                        minimum_bid,
                        current_bid,
                        bid_increment,
                        status,
                        source_url,
                        external_auction_id,
                        last_scraped_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    ) RETURNING auction_id
                """, (
                    self.provider_id,
                    auction_data.get('unit_number', 'N/A'),
                    auction_data.get('unit_size'),
                    auction_data.get('description', ''),
                    auction_data.get('facility_name', ''),
                    auction_data.get('address_line1', ''),
                    auction_data.get('city', 'Unknown'),
                    auction_data.get('state', 'CA'),
                    auction_data.get('zip_code', '00000'),
                    auction_data.get('starts_at', datetime.now()),
                    auction_data.get('closes_at'),
                    auction_data.get('minimum_bid', 0),
                    auction_data.get('current_bid', 0),
                    auction_data.get('bid_increment', 25.00),
                    'active',
                    auction_data.get('source_url'),
                    auction_data.get('external_auction_id')
                ))

                auction_id = cursor.fetchone()['auction_id']

            conn.commit()
            cursor.close()
            conn.close()

            return auction_id

        except Exception as e:
            print(f"Error saving auction: {e}")
            conn.rollback()
            cursor.close()
            conn.close()
            return None

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all auctions from the site
        Override this method in child classes

        Returns:
            List of auction dictionaries
        """
        raise NotImplementedError("Subclasses must implement scrape_all()")

    def scrape_updates(self, auction_ids: List[str]) -> List[Dict]:
        """
        Scrape updates for specific auctions
        Override this method in child classes

        Args:
            auction_ids: List of external auction IDs to update

        Returns:
            List of updated auction dictionaries
        """
        raise NotImplementedError("Subclasses must implement scrape_updates()")

    def log_scrape(self, status: str, auctions_found: int, auctions_added: int, auctions_updated: int, error_message: str = None):
        """
        Log scraping activity to database

        Args:
            status: 'success', 'failed', or 'partial'
            auctions_found: Number of auctions found
            auctions_added: Number of new auctions added
            auctions_updated: Number of existing auctions updated
            error_message: Optional error message if scraping failed
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scrape_logs (
                provider_id,
                scrape_completed_at,
                status,
                auctions_found,
                auctions_added,
                auctions_updated,
                error_message
            ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
        """, (self.provider_id, status, auctions_found, auctions_added, auctions_updated, error_message))

        # Update provider's last_scraped_at
        cursor.execute("""
            UPDATE providers
            SET last_scraped_at = CURRENT_TIMESTAMP
            WHERE provider_id = %s
        """, (self.provider_id,))

        conn.commit()
        cursor.close()
        conn.close()
