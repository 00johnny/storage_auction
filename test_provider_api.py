#!/usr/bin/env python3
"""
Test Provider API Endpoints

This script tests that the provider CRUD endpoints are working correctly.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5000"

def test_create_provider():
    """Test creating a provider"""
    print("Testing POST /api/providers...")

    provider_data = {
        "name": "Test Provider",
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95814",
        "website": "https://test.com",
        "source_url": "https://test.com/auctions",
        "scrape_frequency_hours": 24,
        "is_active": True
    }

    response = requests.post(
        f"{API_BASE_URL}/api/providers",
        json=provider_data,
        headers={'Content-Type': 'application/json'}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response: {response.text[:200]}")

    if response.status_code == 201:
        try:
            result = response.json()
            print(f"✓ Provider created: {result.get('provider_id')}")
            return result.get('provider_id')
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            return None
    else:
        print(f"✗ Failed with status {response.status_code}")
        return None

def test_list_providers():
    """Test listing providers"""
    print("\nTesting GET /api/providers...")

    response = requests.get(f"{API_BASE_URL}/api/providers")

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")

    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✓ Found {len(result.get('providers', []))} providers")
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
    else:
        print(f"✗ Failed with status {response.status_code}")

def test_cors():
    """Test CORS headers"""
    print("\nTesting CORS headers...")

    response = requests.options(
        f"{API_BASE_URL}/api/providers",
        headers={
            'Origin': 'http://test.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
    print(f"Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods')}")

    if 'Access-Control-Allow-Origin' in response.headers:
        print("✓ CORS is configured")
    else:
        print("✗ CORS headers missing")

def main():
    print("=" * 60)
    print("Provider API Endpoint Tests")
    print("=" * 60)

    # Test listing first
    test_list_providers()

    # Test CORS
    test_cors()

    # Test creating
    provider_id = test_create_provider()

    if provider_id:
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        print(f"\nNote: Created test provider with ID: {provider_id}")
        print("You may want to delete this test provider.")
    else:
        print("\n" + "=" * 60)
        print("Some tests failed - check the output above")
        print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        API_BASE_URL = sys.argv[1]

    main()
