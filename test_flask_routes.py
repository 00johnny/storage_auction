#!/usr/bin/env python3
"""
Flask Route Diagnostic Tool

This script tests that Flask routes are working correctly.
Use this to diagnose directory listing or routing issues.
"""

import requests
import sys

API_BASE_URL = "http://localhost:5000"  # Change if different


def test_route(url, expected_content=None):
    """Test a route and report results"""
    try:
        response = requests.get(url, timeout=5)
        status = "✓" if response.status_code == 200 else "✗"

        print(f"{status} {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Not set')}")

        if response.status_code == 200:
            content_preview = response.text[:100].replace('\n', ' ')
            print(f"   Preview: {content_preview}...")

            if expected_content:
                if expected_content in response.text:
                    print(f"   ✓ Contains expected content: '{expected_content}'")
                else:
                    print(f"   ✗ Missing expected content: '{expected_content}'")

        print()
        return response.status_code == 200

    except requests.exceptions.ConnectionError:
        print(f"✗ {url}")
        print(f"   Error: Cannot connect. Is Flask running?")
        print()
        return False
    except Exception as e:
        print(f"✗ {url}")
        print(f"   Error: {e}")
        print()
        return False


def main():
    print("=" * 60)
    print("Flask Route Diagnostic Tool")
    print("=" * 60)
    print(f"Testing: {API_BASE_URL}")
    print()

    tests = [
        (f"{API_BASE_URL}/", "Storage Auction"),
        (f"{API_BASE_URL}/admin", "Admin Portal"),
        (f"{API_BASE_URL}/api/providers", '"success"'),
        (f"{API_BASE_URL}/api/health", '"status"'),
        (f"{API_BASE_URL}/storage-auctions-enhanced.jsx", "StorageAuctionApp"),
    ]

    passed = 0
    failed = 0

    for url, expected in tests:
        if test_route(url, expected):
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    print()

    if failed > 0:
        print("Troubleshooting:")
        print("1. Make sure Flask is running: python3 api_backend.py")
        print("2. Check that you're accessing the correct URL")
        print("3. If seeing directory listing:")
        print("   - You might be accessing Apache/Nginx directly")
        print("   - Make sure requests go through Flask (port 5000)")
        print("   - Check if there's a reverse proxy configuration")
        print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        API_BASE_URL = sys.argv[1]

    main()
