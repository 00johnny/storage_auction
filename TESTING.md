# Testing Guide

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov pytest-mock responses
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=scrapers --cov-report=html

# Run specific test file
pytest tests/test_bid13_scraper.py

# Run with verbose output
pytest -v
```

### Test Categories

Tests are organized into categories:

- **HTML Structure Tests**: Detect if provider HTML changes
- **Parsing Tests**: Validate data extraction logic
- **Edge Case Tests**: Handle malformed or missing data
- **Snapshot Tests**: Alert when significant HTML changes occur

## Writing Tests for New Scrapers

### 1. Create Test Fixture

Save a sample HTML response in `tests/fixtures/`:

```bash
tests/fixtures/
├── bid13_sample.html
├── storageauctions_sample.html
└── your_new_scraper_sample.html
```

### 2. Create Test File

```python
# tests/test_your_scraper.py
import pytest
from bs4 import BeautifulSoup
from scrapers.your_scraper import YourScraper

@pytest.fixture
def sample_html():
    with open('tests/fixtures/your_scraper_sample.html') as f:
        return f.read()

def test_html_structure(sample_html):
    """Detect HTML changes"""
    soup = BeautifulSoup(sample_html, 'html.parser')
    # Test for expected elements
    assert soup.find('div', class_='auction-item') is not None

def test_parsing(sample_html):
    """Test data extraction"""
    scraper = YourScraper('test-provider-id', 'http://test.com')
    # Test parsing logic
    ...
```

### 3. Run Your Tests

```bash
pytest tests/test_your_scraper.py -v
```

## Detecting HTML Changes

When a scraper test fails, it usually means the provider changed their HTML:

1. **Capture new HTML**: Visit the provider's site and save the current HTML
2. **Update fixture**: Replace the fixture file with new HTML
3. **Update scraper**: Modify scraper parsing logic if needed
4. **Update tests**: Adjust test expectations if structure changed
5. **Run tests**: Verify all tests pass with new HTML

## Continuous Testing

### Run Tests Before Committing

```bash
# Add to .git/hooks/pre-commit
pytest
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### Scheduled Test Runs

Run tests periodically to catch HTML changes early:

```bash
# Add to cron (run daily at 2am)
0 2 * * * cd /path/to/storage_auction && pytest --quiet
```

## Test Coverage

View coverage report:

```bash
pytest --cov=scrapers --cov-report=html
# Open htmlcov/index.html in browser
```

Aim for:
- **80%+** code coverage for scrapers
- **100%** coverage for parsing functions
- All edge cases tested

## Mocking External Requests

For integration tests, mock HTTP requests:

```python
import responses

@responses.activate
def test_scrape_with_mock():
    responses.add(
        responses.GET,
        'https://example.com/auctions',
        body='<html>...</html>',
        status=200
    )

    scraper = YourScraper('provider-id', 'https://example.com')
    auctions = scraper.scrape_all()
    assert len(auctions) > 0
```

## Common Test Failures

### "HTML structure may have changed"
- Provider updated their website
- Update fixtures and scraper logic

### "Expected field missing"
- Required data not found in HTML
- Check if provider changed field names/classes

### "Parsing returned None"
- HTML structure significantly different
- Rewrite parsing logic for new structure

## Best Practices

1. **Test with real HTML**: Use actual HTML from provider sites
2. **Update regularly**: Refresh fixtures every few months
3. **Test edge cases**: Empty data, malformed HTML, missing fields
4. **Snapshot important elements**: Test for key CSS classes/IDs
5. **Version fixtures**: Keep old fixtures to track changes over time
