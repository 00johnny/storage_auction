#!/usr/bin/env python3
"""
Test Geocoding

Simple script to test geocoding and show full URLs.

Usage:
    python test_geocoding.py --zipcode 95672
    python test_geocoding.py --city Sacramento --state CA
    python test_geocoding.py --test-url "https://nominatim.openstreetmap.org/search?format=json&limit=1&city=Sacramento&state=CA&country=United+States"
"""

import argparse
import requests
import sys

def test_zipcode(zipcode):
    """Test geocoding a ZIP code"""
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'postalcode': zipcode,
        'country': 'United States',
        'format': 'json',
        'limit': 1
    }

    full_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    print(f"Testing ZIP code: {zipcode}")
    print(f"Full URL: {full_url}")
    print("\nYou can test this URL in your browser or with curl:")
    print(f"curl '{full_url}'")
    print("\nAttempting request...\n")

    try:
        response = requests.get(
            base_url,
            params=params,
            headers={'User-Agent': 'StorageAuctionPlatform/1.0'},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            results = response.json()
            if results:
                print(f"\n✓ Success! Found {len(results)} result(s)")
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Display Name: {result.get('display_name')}")
                    print(f"  Latitude: {result.get('lat')}")
                    print(f"  Longitude: {result.get('lon')}")
            else:
                print("\n✗ No results found for this ZIP code")
        else:
            print(f"\n✗ Request failed with status {response.status_code}")

    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ Connection Error: {e}")
        print("\nThis usually means:")
        print("  1. No internet connection")
        print("  2. Firewall blocking the request")
        print("  3. DNS resolution failing")
    except Exception as e:
        print(f"\n✗ Error: {e}")

def test_city_state(city, state):
    """Test geocoding a city/state"""
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'city': city,
        'state': state,
        'country': 'United States',
        'format': 'json',
        'limit': 1
    }

    full_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    print(f"Testing City/State: {city}, {state}")
    print(f"Full URL: {full_url}")
    print("\nYou can test this URL in your browser or with curl:")
    print(f"curl '{full_url}'")
    print("\nAttempting request...\n")

    try:
        response = requests.get(
            base_url,
            params=params,
            headers={'User-Agent': 'StorageAuctionPlatform/1.0'},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            results = response.json()
            if results:
                print(f"\n✓ Success! Found {len(results)} result(s)")
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Display Name: {result.get('display_name')}")
                    print(f"  Latitude: {result.get('lat')}")
                    print(f"  Longitude: {result.get('lon')}")
            else:
                print("\n✗ No results found for this city/state")
        else:
            print(f"\n✗ Request failed with status {response.status_code}")

    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ Connection Error: {e}")
        print("\nThis usually means:")
        print("  1. No internet connection")
        print("  2. Firewall blocking the request")
        print("  3. DNS resolution failing")
    except Exception as e:
        print(f"\n✗ Error: {e}")

def test_url(url):
    """Test a direct URL"""
    print(f"Testing URL: {url}")
    print("\nAttempting request...\n")

    try:
        response = requests.get(
            url,
            headers={'User-Agent': 'StorageAuctionPlatform/1.0'},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            results = response.json()
            if results:
                print(f"\n✓ Success! Found {len(results)} result(s)")
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"  Display Name: {result.get('display_name')}")
                    print(f"  Latitude: {result.get('lat')}")
                    print(f"  Longitude: {result.get('lon')}")
            else:
                print("\n✗ No results found")
        else:
            print(f"\n✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test geocoding API')
    parser.add_argument('--zipcode', help='Test a ZIP code')
    parser.add_argument('--city', help='Test a city')
    parser.add_argument('--state', help='Test a state (use with --city)')
    parser.add_argument('--test-url', help='Test a direct URL')

    args = parser.parse_args()

    if args.test_url:
        test_url(args.test_url)
    elif args.zipcode:
        test_zipcode(args.zipcode)
    elif args.city and args.state:
        test_city_state(args.city, args.state)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python test_geocoding.py --zipcode 95672")
        print("  python test_geocoding.py --city Sacramento --state CA")
        print("  python test_geocoding.py --city 'Cameron Park' --state CA")

if __name__ == '__main__':
    main()
