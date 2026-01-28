#!/usr/bin/env python3
"""
Migration Runner - Applies database migrations

Usage: python run_migration.py migrations/add_geocoding_cache.sql
"""

import sys
import os
import psycopg2
from dotenv import load_dotenv

def run_migration(migration_file):
    """Run a SQL migration file"""
    # Load environment variables
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')

    print(f"Running migration: {migration_file}")

    # Read migration file
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Execute migration
        cursor.execute(sql)
        conn.commit()
        print(f"✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        sys.exit(1)

    migration_file = sys.argv[1]

    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)

    run_migration(migration_file)
