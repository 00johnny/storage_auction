"""
Simple Geocoding Helper

Provides basic geocoding functionality for city/state lookups
without requiring external API keys. Uses OpenStreetMap Nominatim
(free, no API key required).
"""

import requests
import time
from typing import Optional, Tuple

class SimpleGeocoder:
    """Simple geocoder using OpenStreetMap Nominatim"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            'User-Agent': 'StorageAuctionPlatform/1.0'
        }
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Nominatim requires 1 second between requests
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def geocode_city_state(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a city and state to latitude/longitude
        
        Args:
            city: City name (e.g., "Sacramento")
            state: State code (e.g., "CA")
        
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            self._rate_limit()
            
            params = {
                'city': city,
                'state': state,
                'country': 'United States',
                'format': 'json',
                'limit': 1
            }
            
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
                return (lat, lon)
            
            return None
            
        except Exception as e:
            print(f"Geocoding error for {city}, {state}: {e}")
            return None
    
    def geocode_zipcode(self, zipcode: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a ZIP code to latitude/longitude
        
        Args:
            zipcode: 5-digit ZIP code
        
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            self._rate_limit()
            
            params = {
                'postalcode': zipcode,
                'country': 'United States',
                'format': 'json',
                'limit': 1
            }
            
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
                return (lat, lon)
            
            return None
            
        except Exception as e:
            print(f"Geocoding error for zipcode {zipcode}: {e}")
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
