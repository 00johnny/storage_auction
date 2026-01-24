#!/bin/bash
#
# Flask Startup Script
#
# This script ensures Flask runs correctly with proper configuration
#

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with DATABASE_URL and API_BASE_URL"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "========================================="
echo "Storage Auction Platform - Flask Server"
echo "========================================="
echo ""
echo "Starting Flask application..."
echo "API will be available at: $API_BASE_URL"
echo ""
echo "Available routes:"
echo "  / - Frontend"
echo "  /admin - Admin Portal"
echo "  /api/* - API Endpoints"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

# Run Flask
python3 api_backend.py
