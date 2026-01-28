"""
Unit tests for Bid13 scraper

Tests parsing logic, HTML structure detection, and data mapping
"""

import pytest
from bs4 import BeautifulSoup
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bid13_scraper import Bid13Scraper


@pytest.fixture
def sample_html():
    """Load sample HTML fixture"""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'bid13_sample.html')
    with open(fixture_path, 'r') as f:
        return f.read()


@pytest.fixture
def scraper():
    """Create a scraper instance for testing"""
    # Use a test provider ID
    return Bid13Scraper(
        provider_id='00000000-0000-0000-0000-000000000000',
        facility_url='https://bid13.com/test'
    )


class TestBid13HTMLStructure:
    """Tests to detect if Bid13 changes their HTML structure"""

    def test_auction_list_container_exists(self, sample_html):
        """Test that auction list container exists"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auctions = soup.find_all('li', {"class": 'auction-search-result'})
        assert len(auctions) > 0, "No auction items found - HTML structure may have changed"

    def test_auction_link_structure(self, sample_html):
        """Test that auction link structure is intact"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction = soup.find('li', {"class": 'auction-search-result'})

        link = auction.find('a', class_='auction-link-wrapper')
        assert link is not None, "Auction link wrapper not found"
        assert link.get('data-node-id') is not None, "data-node-id attribute missing"
        assert link.get('href') is not None, "href attribute missing"

    def test_unit_title_exists(self, sample_html):
        """Test that unit title element exists"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction = soup.find('li', {"class": 'auction-search-result'})

        title = auction.find('span', class_='title')
        assert title is not None, "Unit title element not found"
        assert title.text.strip() != '', "Unit title is empty"

    def test_unit_size_exists(self, sample_html):
        """Test that unit size element exists"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction = soup.find('li', {"class": 'auction-search-result'})

        size = auction.find('span', class_='unit-size')
        assert size is not None, "Unit size element not found"

    def test_current_bid_exists(self, sample_html):
        """Test that current bid element exists"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction = soup.find('li', {"class": 'auction-search-result'})

        bid = auction.find('div', class_='auc-current-bid')
        assert bid is not None, "Current bid element not found"
        assert '$' in bid.text, "Bid amount doesn't contain dollar sign"

    def test_countdown_expiry_exists(self, sample_html):
        """Test that countdown expiry data exists"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction = soup.find('li', {"class": 'auction-search-result'})

        countdown = auction.find('div', class_='countdown')
        assert countdown is not None, "Countdown element not found"
        assert countdown.get('data-expiry') is not None, "data-expiry attribute missing"


class TestBid13Parsing:
    """Tests for parsing logic"""

    def test_parse_auction_basic(self, scraper, sample_html):
        """Test basic auction parsing"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert result is not None, "Parsing returned None"
        assert result['external_auction_id'] == '12345'
        assert result['unit_number'] == 'Unit A-127'
        assert result['unit_size'] == '10x10'
        assert result['current_bid'] == 450.0
        assert result['source_url'] is not None

    def test_parse_multiple_auctions(self, scraper, sample_html):
        """Test parsing multiple auctions"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction_elems = soup.find_all('li', {"class": 'auction-search-result'})

        results = [scraper._parse_auction(elem) for elem in auction_elems]
        results = [r for r in results if r is not None]

        assert len(results) == 2, f"Expected 2 auctions, got {len(results)}"

        # Check first auction
        assert results[0]['external_auction_id'] == '12345'
        assert results[0]['unit_number'] == 'Unit A-127'

        # Check second auction
        assert results[1]['external_auction_id'] == '12346'
        assert results[1]['unit_number'] == 'Unit B-45'

    def test_bid_amount_parsing(self, scraper, sample_html):
        """Test that bid amounts are correctly parsed"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert isinstance(result['current_bid'], float), "Bid should be float"
        assert result['current_bid'] == 450.0
        assert result['minimum_bid'] == 450.0  # Same as current for first bid

    def test_datetime_parsing(self, scraper, sample_html):
        """Test that datetimes are correctly parsed"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert result['closes_at'] is not None, "closes_at should not be None"
        assert isinstance(result['closes_at'], datetime), "closes_at should be datetime"

    def test_required_fields_present(self, scraper, sample_html):
        """Test that all required database fields are present"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        required_fields = [
            'external_auction_id', 'unit_number', 'description',
            'city', 'state', 'zip_code', 'closes_at',
            'current_bid', 'minimum_bid', 'source_url'
        ]

        for field in required_fields:
            assert field in result, f"Required field '{field}' missing"
            assert result[field] is not None, f"Required field '{field}' is None"


class TestBid13EdgeCases:
    """Tests for edge cases and error handling"""

    def test_missing_optional_fields(self, scraper):
        """Test handling of missing optional fields"""
        html = """
        <li class="auction-search-result">
            <a class="auction-link-wrapper" data-node-id="99999" href="/auction/99999">
                <span class="title">Unit Z-1</span>
            </a>
            <div class="auc-current-bid">$100</div>
            <div class="countdown" data-expiry="2026-02-20T10:00:00"></div>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert result is not None, "Should handle missing optional fields"
        assert result['unit_size'] is None, "Missing unit_size should be None"

    def test_malformed_bid_amount(self, scraper):
        """Test handling of malformed bid amounts"""
        html = """
        <li class="auction-search-result">
            <a class="auction-link-wrapper" data-node-id="99999" href="/auction/99999">
                <span class="title">Unit Z-1</span>
            </a>
            <div class="auc-current-bid">INVALID</div>
            <div class="countdown" data-expiry="2026-02-20T10:00:00"></div>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert result is not None, "Should handle malformed bid"
        assert result['current_bid'] == 0, "Malformed bid should default to 0"

    def test_missing_node_link(self, scraper):
        """Test handling of missing node link"""
        html = """
        <li class="auction-search-result">
            <span class="title">Unit Z-1</span>
        </li>
        """
        soup = BeautifulSoup(html, 'html.parser')
        auction_elem = soup.find('li', {"class": 'auction-search-result'})

        result = scraper._parse_auction(auction_elem)

        assert result is None, "Should return None for invalid auction"


def test_html_structure_snapshot(sample_html):
    """
    Snapshot test to detect HTML structure changes

    This test will fail if Bid13 significantly changes their HTML,
    alerting you to update the scraper.
    """
    soup = BeautifulSoup(sample_html, 'html.parser')

    # Expected structure signature
    expected_classes = [
        'auction-search-result',
        'auction-link-wrapper',
        'title',
        'unit-size',
        'auc-current-bid',
        'countdown'
    ]

    found_classes = set()
    for elem in soup.find_all(class_=True):
        for cls in elem.get('class', []):
            found_classes.add(cls)

    for expected in expected_classes:
        assert expected in found_classes, f"Expected CSS class '{expected}' not found in HTML - structure may have changed"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
