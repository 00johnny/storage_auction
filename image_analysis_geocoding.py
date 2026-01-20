"""
Storage Auction Image Analysis and Geocoding Script

This script handles:
1. AI-powered image analysis for auction photos
2. Address geocoding with fallback to city-level coordinates
3. Automatic tag generation from image content

Dependencies:
    pip install requests pillow --break-system-packages
    
For AI Analysis, choose one of:
    - Google Cloud Vision API (free tier available)
    - Azure Computer Vision (free tier available)  
    - Hugging Face transformers (free, local)
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os


class GeocodeService:
    """Handle address geocoding with multiple fallback options"""
    
    def __init__(self):
        self.nominatim_base = "https://nominatim.openstreetmap.org"
        self.user_agent = "StorageAuctionApp/1.0"
        
    def geocode_address(self, address: str, city: str, state: str, zip_code: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to lat/long coordinates
        
        Args:
            address: Street address
            city: City name
            state: State abbreviation
            zip_code: Zip code
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        # Try full address first
        full_address = f"{address}, {city}, {state} {zip_code}"
        coords = self._geocode_nominatim(full_address)
        
        if coords:
            return coords
            
        # Fallback to city + state
        print(f"Full address geocoding failed, trying city-level for {city}, {state}")
        city_address = f"{city}, {state}, USA"
        coords = self._geocode_nominatim(city_address)
        
        if coords:
            return coords
            
        # Last resort: state center
        print(f"City geocoding failed, using state center for {state}")
        return self._get_state_center(state)
    
    def _geocode_nominatim(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Use Nominatim (OpenStreetMap) to geocode an address
        Free tier: Max 1 request per second
        """
        try:
            # Respect rate limiting
            time.sleep(1)
            
            url = f"{self.nominatim_base}/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"✓ Geocoded: {address} -> ({lat}, {lon})")
                return (lat, lon)
            
            return None
            
        except Exception as e:
            print(f"✗ Geocoding error: {e}")
            return None
    
    def _get_state_center(self, state: str) -> Optional[Tuple[float, float]]:
        """Fallback to approximate state centers"""
        state_centers = {
            'CA': (36.7783, -119.4179),  # California
            'TX': (31.9686, -99.9018),   # Texas
            'NY': (43.2994, -74.2179),   # New York
            'FL': (27.6648, -81.5158),   # Florida
            # Add more states as needed
        }
        return state_centers.get(state.upper())


class ImageAnalysisService:
    """Handle AI image analysis for auction photos"""
    
    def __init__(self, service_type: str = 'huggingface'):
        """
        Initialize image analysis service
        
        Args:
            service_type: 'google', 'azure', or 'huggingface'
        """
        self.service_type = service_type
        
    def analyze_image(self, image_url: str) -> Dict:
        """
        Analyze an image and return detected objects, descriptions, and tags
        
        Args:
            image_url: URL or path to image
            
        Returns:
            Dict with keys: description, objects, tags, confidence
        """
        if self.service_type == 'huggingface':
            return self._analyze_huggingface(image_url)
        elif self.service_type == 'google':
            return self._analyze_google_vision(image_url)
        elif self.service_type == 'azure':
            return self._analyze_azure_vision(image_url)
        else:
            raise ValueError(f"Unknown service type: {self.service_type}")
    
    def _analyze_huggingface(self, image_url: str) -> Dict:
        """
        Use Hugging Face Inference API (free)
        Model: BLIP or CLIP for image captioning
        """
        try:
            # Using BLIP image captioning model
            API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
            
            # You'll need a Hugging Face API token (free)
            # Get one at: https://huggingface.co/settings/tokens
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN', '')}"}
            
            # For image URL
            response = requests.post(API_URL, headers=headers, json={"inputs": image_url})
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                description = result[0].get('generated_text', '')
                
                # Extract tags from description
                tags = self._extract_tags_from_description(description)
                
                return {
                    'description': description,
                    'objects': [],  # BLIP doesn't provide object detection
                    'tags': tags,
                    'confidence': 0.85,
                    'analyzed_at': datetime.now().isoformat()
                }
            
            return self._empty_result()
            
        except Exception as e:
            print(f"✗ Hugging Face analysis error: {e}")
            return self._empty_result()
    
    def _analyze_google_vision(self, image_url: str) -> Dict:
        """
        Use Google Cloud Vision API
        Free tier: 1000 requests/month
        """
        try:
            api_key = os.getenv('GOOGLE_VISION_API_KEY', '')
            if not api_key:
                print("✗ Google Vision API key not found")
                return self._empty_result()
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            
            payload = {
                "requests": [{
                    "image": {"source": {"imageUri": image_url}},
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 10},
                        {"type": "OBJECT_LOCALIZATION", "maxResults": 10}
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'responses' in result and len(result['responses']) > 0:
                resp = result['responses'][0]
                
                # Extract labels and objects
                labels = [label['description'] for label in resp.get('labelAnnotations', [])]
                objects = [obj['name'] for obj in resp.get('localizedObjectAnnotations', [])]
                
                # Generate description
                description = f"Detected: {', '.join(objects[:5] if objects else labels[:5])}"
                
                # Generate tags
                tags = self._generate_tags(labels + objects)
                
                return {
                    'description': description,
                    'objects': objects,
                    'tags': tags,
                    'confidence': 0.90,
                    'analyzed_at': datetime.now().isoformat()
                }
            
            return self._empty_result()
            
        except Exception as e:
            print(f"✗ Google Vision error: {e}")
            return self._empty_result()
    
    def _analyze_azure_vision(self, image_url: str) -> Dict:
        """
        Use Azure Computer Vision API
        Free tier: 5000 requests/month
        """
        try:
            endpoint = os.getenv('AZURE_VISION_ENDPOINT', '')
            key = os.getenv('AZURE_VISION_KEY', '')
            
            if not endpoint or not key:
                print("✗ Azure Vision credentials not found")
                return self._empty_result()
            
            url = f"{endpoint}/vision/v3.2/analyze"
            headers = {
                'Ocp-Apim-Subscription-Key': key,
                'Content-Type': 'application/json'
            }
            params = {
                'visualFeatures': 'Categories,Tags,Description,Objects',
                'language': 'en'
            }
            body = {'url': image_url}
            
            response = requests.post(url, headers=headers, params=params, json=body, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Extract information
            description = result.get('description', {}).get('captions', [{}])[0].get('text', '')
            tags = [tag['name'] for tag in result.get('tags', [])]
            objects = [obj['object'] for obj in result.get('objects', [])]
            
            generated_tags = self._generate_tags(tags + objects)
            
            return {
                'description': description,
                'objects': objects,
                'tags': generated_tags,
                'confidence': 0.88,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"✗ Azure Vision error: {e}")
            return self._empty_result()
    
    def _extract_tags_from_description(self, description: str) -> List[str]:
        """Extract relevant tags from a text description"""
        # Simple keyword matching - could be improved with NLP
        keywords = {
            'furniture': ['furniture', 'chair', 'table', 'couch', 'sofa', 'dresser', 'bed'],
            'electronics': ['electronics', 'tv', 'television', 'computer', 'laptop', 'monitor'],
            'tools': ['tools', 'drill', 'saw', 'hammer', 'equipment'],
            'boxes': ['box', 'boxes', 'container', 'storage'],
            'appliances': ['appliance', 'refrigerator', 'washer', 'dryer', 'microwave'],
            'sports': ['sports', 'bike', 'bicycle', 'golf', 'tennis', 'exercise'],
            'office': ['office', 'desk', 'filing', 'cabinet'],
            'household': ['household', 'items', 'belongings']
        }
        
        description_lower = description.lower()
        tags = []
        
        for tag, words in keywords.items():
            if any(word in description_lower for word in words):
                tags.append(tag)
        
        return tags if tags else ['miscellaneous']
    
    def _generate_tags(self, detected_items: List[str]) -> List[str]:
        """Generate standardized tags from detected items"""
        tag_mapping = {
            'furniture': ['furniture', 'chair', 'table', 'couch', 'sofa', 'dresser', 'bed', 'shelf'],
            'electronics': ['electronics', 'television', 'computer', 'laptop', 'monitor', 'screen'],
            'tools': ['tool', 'drill', 'saw', 'hammer', 'equipment', 'toolbox'],
            'boxes': ['box', 'container', 'storage bin', 'cardboard'],
            'appliances': ['appliance', 'refrigerator', 'washer', 'dryer', 'microwave', 'stove'],
            'sports': ['sports equipment', 'bicycle', 'bike', 'golf club', 'tennis racket'],
            'office': ['office furniture', 'desk', 'filing cabinet', 'office chair'],
            'household': ['household item', 'home decor', 'kitchenware'],
            'outdoor': ['outdoor', 'camping', 'tent', 'backpack', 'hiking'],
            'premium': []  # Manually assigned based on condition
        }
        
        tags = set()
        for item in detected_items:
            item_lower = item.lower()
            for tag, keywords in tag_mapping.items():
                if any(keyword in item_lower for keyword in keywords):
                    tags.add(tag)
        
        return list(tags) if tags else ['miscellaneous']
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'description': '',
            'objects': [],
            'tags': ['miscellaneous'],
            'confidence': 0.0,
            'analyzed_at': datetime.now().isoformat()
        }


# Example usage
def process_auction_images(auction_id: str, image_urls: List[str], 
                          address: str, city: str, state: str, zip_code: str):
    """
    Complete workflow for processing auction data
    
    Args:
        auction_id: Unique auction identifier
        image_urls: List of image URLs to analyze
        address: Street address
        city: City name
        state: State code
        zip_code: Zip code
    """
    print(f"\n{'='*60}")
    print(f"Processing Auction: {auction_id}")
    print(f"{'='*60}\n")
    
    # 1. Geocode address
    print("📍 Geocoding address...")
    geocoder = GeocodeService()
    coords = geocoder.geocode_address(address, city, state, zip_code)
    
    if coords:
        latitude, longitude = coords
        print(f"✓ Coordinates: {latitude}, {longitude}\n")
    else:
        print("✗ Geocoding failed\n")
        latitude, longitude = None, None
    
    # 2. Analyze images
    print("🖼️  Analyzing images...")
    analyzer = ImageAnalysisService(service_type='huggingface')
    
    all_tags = set()
    descriptions = []
    
    for i, image_url in enumerate(image_urls, 1):
        print(f"\n  Image {i}/{len(image_urls)}: {image_url}")
        result = analyzer.analyze_image(image_url)
        
        if result['description']:
            descriptions.append(result['description'])
            all_tags.update(result['tags'])
            print(f"  ✓ Description: {result['description']}")
            print(f"  ✓ Tags: {', '.join(result['tags'])}")
        else:
            print(f"  ✗ Analysis failed")
    
    # 3. Compile results
    final_description = " | ".join(descriptions) if descriptions else "No AI analysis available"
    final_tags = list(all_tags)
    
    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"{'='*60}")
    print(f"Coordinates: ({latitude}, {longitude})")
    print(f"AI Description: {final_description}")
    print(f"Tags: {', '.join(final_tags)}")
    print(f"{'='*60}\n")
    
    return {
        'auction_id': auction_id,
        'latitude': latitude,
        'longitude': longitude,
        'ai_description': final_description,
        'tags': final_tags,
        'analyzed_at': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Example: Process a sample auction
    
    # Set your API keys as environment variables:
    # export HUGGINGFACE_API_TOKEN="your_token_here"
    # export GOOGLE_VISION_API_KEY="your_key_here"
    # export AZURE_VISION_ENDPOINT="your_endpoint_here"
    # export AZURE_VISION_KEY="your_key_here"
    
    sample_result = process_auction_images(
        auction_id="A-127",
        image_urls=[
            "https://via.placeholder.com/800x600?text=Storage+Unit+Image"
        ],
        address="1234 Main St",
        city="Sacramento",
        state="CA",
        zip_code="95814"
    )
    
    print("Sample result:", json.dumps(sample_result, indent=2))
