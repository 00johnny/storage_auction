"""
Image Analysis Service

Analyzes storage unit auction images to:
- Identify visible items
- Estimate fullness (0-100%)
- Categorize items
- Generate detailed descriptions

Supports multiple AI providers with easy swapping:
- Hugging Face (free tier)
- OpenAI GPT-4 Vision (paid)
- Anthropic Claude Vision (paid)
"""

import requests
import os
from typing import Dict, List, Optional
from abc import ABC, abstractmethod


class ImageAnalyzerBase(ABC):
    """Base class for image analyzers - allows easy provider swapping"""

    @abstractmethod
    def analyze_image(self, image_url: str) -> Dict:
        """
        Analyze a storage unit image

        Args:
            image_url: URL of the image to analyze

        Returns:
            {
                'description': str,  # Detailed description of items
                'fullness_rating': int,  # 0-100
                'items': List[str],  # List of visible items
                'categories': List[str],  # Item categories
                'condition': str,  # 'empty', 'sparse', 'moderate', 'full', 'packed'
                'valuable_items': bool  # Whether potentially valuable items visible
            }
        """
        pass


class HuggingFaceAnalyzer(ImageAnalyzerBase):
    """
    Hugging Face image analysis using BLIP-2 or similar models
    Free tier with rate limits
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Hugging Face analyzer

        Args:
            api_token: HF API token (optional, uses env var if not provided)
        """
        self.api_token = api_token or os.getenv('HUGGINGFACE_API_TOKEN')
        self.api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    def analyze_image(self, image_url: str) -> Dict:
        """Analyze image using Hugging Face BLIP model"""
        try:
            # Download image
            image_response = requests.get(image_url, timeout=10)
            image_response.raise_for_status()
            image_data = image_response.content

            # Send to Hugging Face API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=image_data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Extract caption from HF response
            if isinstance(result, list) and len(result) > 0:
                caption = result[0].get('generated_text', '')
            else:
                caption = result.get('generated_text', '')

            # Parse caption to extract insights
            parsed = self._parse_caption(caption)

            return parsed

        except Exception as e:
            print(f"HuggingFace analysis error: {e}")
            return self._empty_result(f"Error: {str(e)}")

    def _parse_caption(self, caption: str) -> Dict:
        """Parse BLIP caption into structured data"""
        caption_lower = caption.lower()

        # Estimate fullness based on keywords
        fullness = 50  # default
        if any(word in caption_lower for word in ['empty', 'bare', 'vacant']):
            fullness = 10
        elif any(word in caption_lower for word in ['few', 'sparse', 'some']):
            fullness = 30
        elif any(word in caption_lower for word in ['many', 'several', 'multiple']):
            fullness = 60
        elif any(word in caption_lower for word in ['full', 'packed', 'filled', 'crowded']):
            fullness = 85

        # Extract items mentioned
        items = self._extract_items(caption)

        # Categorize
        categories = self._categorize_items(items, caption_lower)

        # Determine condition
        condition = self._estimate_condition(fullness)

        # Check for valuable items
        valuable_keywords = ['furniture', 'appliance', 'electronics', 'antique', 'tools']
        valuable_items = any(keyword in caption_lower for keyword in valuable_keywords)

        return {
            'description': caption,
            'fullness_rating': fullness,
            'items': items,
            'categories': categories,
            'condition': condition,
            'valuable_items': valuable_items
        }

    def _extract_items(self, caption: str) -> List[str]:
        """Extract item names from caption"""
        common_items = [
            'box', 'boxes', 'furniture', 'chair', 'table', 'couch', 'sofa',
            'bed', 'mattress', 'dresser', 'cabinet', 'shelf', 'shelves',
            'appliance', 'refrigerator', 'washer', 'dryer', 'tv', 'television',
            'lamp', 'mirror', 'picture', 'frame', 'bag', 'bags', 'tote',
            'container', 'bin', 'crate', 'tool', 'tools', 'bicycle', 'bike',
            'clothing', 'clothes', 'books', 'electronics'
        ]

        caption_lower = caption.lower()
        found_items = [item for item in common_items if item in caption_lower]
        return found_items[:10]  # Limit to 10 items

    def _categorize_items(self, items: List[str], caption: str) -> List[str]:
        """Categorize items into broad categories"""
        categories = set()

        furniture_words = ['furniture', 'chair', 'table', 'couch', 'sofa', 'bed', 'dresser', 'cabinet']
        appliance_words = ['appliance', 'refrigerator', 'washer', 'dryer', 'tv']
        storage_words = ['box', 'boxes', 'bag', 'container', 'bin', 'crate']

        if any(word in caption for word in furniture_words):
            categories.add('furniture')
        if any(word in caption for word in appliance_words):
            categories.add('appliances')
        if any(word in caption for word in storage_words):
            categories.add('boxes/containers')
        if 'tool' in caption or 'tools' in caption:
            categories.add('tools')
        if 'clothing' in caption or 'clothes' in caption:
            categories.add('clothing')

        return list(categories)

    def _estimate_condition(self, fullness: int) -> str:
        """Estimate condition based on fullness"""
        if fullness < 15:
            return 'empty'
        elif fullness < 35:
            return 'sparse'
        elif fullness < 65:
            return 'moderate'
        elif fullness < 85:
            return 'full'
        else:
            return 'packed'

    def _empty_result(self, description: str) -> Dict:
        """Return empty result structure"""
        return {
            'description': description,
            'fullness_rating': 50,
            'items': [],
            'categories': [],
            'condition': 'unknown',
            'valuable_items': False
        }


class OpenAIVisionAnalyzer(ImageAnalyzerBase):
    """
    OpenAI GPT-4 Vision analyzer (for future use)
    Requires OpenAI API key and has per-request costs
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def analyze_image(self, image_url: str) -> Dict:
        """Analyze using GPT-4 Vision (placeholder for future implementation)"""
        if not self.api_key:
            return {
                'description': 'OpenAI API key not configured',
                'fullness_rating': 50,
                'items': [],
                'categories': [],
                'condition': 'unknown',
                'valuable_items': False
            }

        # TODO: Implement GPT-4 Vision API call
        # Would use more sophisticated prompting for better results
        raise NotImplementedError("OpenAI Vision not yet implemented")


class ClaudeVisionAnalyzer(ImageAnalyzerBase):
    """
    Anthropic Claude Vision analyzer (for future use)
    Requires Anthropic API key and has per-request costs
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.api_url = "https://api.anthropic.com/v1/messages"

    def analyze_image(self, image_url: str) -> Dict:
        """Analyze using Claude Vision (placeholder for future implementation)"""
        if not self.api_key:
            return {
                'description': 'Anthropic API key not configured',
                'fullness_rating': 50,
                'items': [],
                'categories': [],
                'condition': 'unknown',
                'valuable_items': False
            }

        # TODO: Implement Claude Vision API call
        raise NotImplementedError("Claude Vision not yet implemented")


class ImageAnalysisService:
    """
    Main service for image analysis - handles provider selection and caching
    """

    def __init__(self, provider: str = 'huggingface'):
        """
        Initialize image analysis service

        Args:
            provider: 'huggingface', 'openai', or 'claude'
        """
        self.provider = provider
        self.analyzer = self._create_analyzer(provider)

    def _create_analyzer(self, provider: str) -> ImageAnalyzerBase:
        """Factory method to create appropriate analyzer"""
        if provider == 'huggingface':
            return HuggingFaceAnalyzer()
        elif provider == 'openai':
            return OpenAIVisionAnalyzer()
        elif provider == 'claude':
            return ClaudeVisionAnalyzer()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def analyze_storage_unit(self, image_url: str) -> Dict:
        """
        Analyze a storage unit image

        Args:
            image_url: URL of the image to analyze

        Returns:
            Analysis results dictionary
        """
        return self.analyzer.analyze_image(image_url)

    def analyze_multiple_images(self, image_urls: List[str]) -> Dict:
        """
        Analyze multiple images and combine results

        Args:
            image_urls: List of image URLs

        Returns:
            Combined analysis results
        """
        if not image_urls:
            return self.analyzer._empty_result("No images provided")

        # Analyze first image (or could analyze all and combine)
        # For now, just use the first image to save API calls
        primary_result = self.analyze_storage_unit(image_urls[0])

        # Could enhance by analyzing multiple images and combining insights
        primary_result['images_analyzed'] = 1
        primary_result['total_images'] = len(image_urls)

        return primary_result


# Convenience function
def analyze_auction_images(image_urls: List[str], provider: str = 'huggingface') -> Dict:
    """
    Convenience function to analyze auction images

    Args:
        image_urls: List of image URLs
        provider: AI provider to use

    Returns:
        Analysis results
    """
    service = ImageAnalysisService(provider=provider)
    return service.analyze_multiple_images(image_urls)
