"""
Simple Geocoding Helper

Provides basic geocoding functionality for city/state lookups
without requiring external API keys. Uses OpenStreetMap Nominatim
(free, no API key required).

Includes database caching to dramatically improve performance and
reduce API calls to Nominatim.
"""

import requests
import time
from typing import Optional, Tuple

class SimpleGeocoder:
    """Simple geocoder using OpenStreetMap Nominatim with database caching"""

    def __init__(self, db_connection=None):
        """
        Initialize geocoder with optional database connection for caching

        Args:
            db_connection: psycopg2 connection object for cache storage (optional)
        """
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'StorageAuctionPlatform/1.0'
        }
        self._last_request_time = 0
        self._min_request_interval = 1.5  # 1.5 seconds between requests (safer than minimum 1.0)
        self.db_connection = db_connection

    def _check_cache(self, location_type: str, location_key: str) -> Optional[Tuple[float, float]]:
        """
        Check database cache for geocoded location

        Args:
            location_type: 'zipcode' or 'city_state'
            location_key: The location identifier (e.g., '95672' or 'Sacramento,CA')

        Returns:
            Tuple of (latitude, longitude) or None if not in cache
        """
        if not self.db_connection:
            return None

        try:
            from psycopg2.extras import RealDictCursor
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                UPDATE geocoded_locations
                SET hit_count = hit_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE location_type = %s AND location_key = %s
                RETURNING latitude, longitude
            """, (location_type, location_key))

            result = cursor.fetchone()
            self.db_connection.commit()
            cursor.close()

            if result:
                return (float(result['latitude']), float(result['longitude']))

            return None

        except Exception as e:
            print(f"Cache check error: {e}")
            return None

    def _save_to_cache(self, location_type: str, location_key: str, lat: float, lon: float):
        """
        Save geocoded location to database cache

        Args:
            location_type: 'zipcode' or 'city_state'
            location_key: The location identifier
            lat: Latitude
            lon: Longitude
        """
        if not self.db_connection:
            return

        try:
            from psycopg2.extras import RealDictCursor
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                INSERT INTO geocoded_locations (location_type, location_key, latitude, longitude, hit_count)
                VALUES (%s, %s, %s, %s, 1)
                ON CONFLICT (location_type, location_key)
                DO UPDATE SET
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    updated_at = CURRENT_TIMESTAMP
            """, (location_type, location_key, lat, lon))

            self.db_connection.commit()
            cursor.close()

        except Exception as e:
            print(f"Cache save error: {e}")

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def geocode_city_state(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a city and state to latitude/longitude

        Checks database cache first, only makes API call if not cached.

        Args:
            city: City name (e.g., "Sacramento")
            state: State code (e.g., "CA")

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Create cache key
        location_key = f"{city},{state}"

        # Check cache first
        cached = self._check_cache('city_state', location_key)
        if cached:
            return cached

        # Not in cache, make API call
        try:
            self._rate_limit()

            params = {
                'city': city,
                'state': state,
                'country': 'United States',
                'format': 'json',
                'limit': 1
            }

            # Build full URL for logging
            full_url = f"{self.base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()

            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])

                # Save to cache
                self._save_to_cache('city_state', location_key, lat, lon)

                return (lat, lon)

            return None

        except Exception as e:
            print(f"Geocoding error for {city}, {state}: {e}")
            print(f"Full URL: {full_url}")
            return None
    
    def geocode_zipcode(self, zipcode: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a ZIP code to latitude/longitude

        Checks database cache first, only makes API call if not cached.

        Args:
            zipcode: 5-digit ZIP code

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Check cache first
        cached = self._check_cache('zipcode', zipcode)
        if cached:
            return cached

        # Not in cache, make API call
        try:
            self._rate_limit()

            params = {
                'postalcode': zipcode,
                'country': 'United States',
                'format': 'json',
                'limit': 1
            }

            # Build full URL for logging
            full_url = f"{self.base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()

            results = response.json()
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])

                # Save to cache
                self._save_to_cache('zipcode', zipcode, lat, lon)

                return (lat, lon)

            return None

        except Exception as e:
            print(f"Geocoding error for zipcode {zipcode}: {e}")
            print(f"Full URL: {full_url}")
            return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in miles
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth's radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance
