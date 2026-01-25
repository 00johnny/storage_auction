# Storage Auction Platform - Recent Improvements

## Overview

This document summarizes the major improvements made to the storage auction platform, focusing on facility management, scraper enhancements, and testing capabilities.

---

## 1. Facilities Table

### Problem
Previously, auction records stored location data (city, state, facility name) directly in each auction record. This caused:
- Duplicate address information across multiple auctions
- Difficulty maintaining consistent facility data
- No way to link auctions to their physical storage location

### Solution
Created a new `facilities` table to store physical storage locations:

```sql
CREATE TABLE facilities (
    facility_id UUID PRIMARY KEY,
    provider_id UUID NOT NULL,
    facility_name VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10),
    -- ... other fields
    UNIQUE(provider_id, facility_name, city, state)
);
```

**Key Features:**
- Facilities are uniquely identified by: `(provider_id, facility_name, city, state)`
- Multiple auctions can reference the same facility via `facility_id`
- Auctions still keep denormalized location data for fast queries
- Full address info can be stored once per facility and looked up later

**Usage:**
```python
# Scraper automatically creates or looks up facility
facility_data = {
    'facility_name': 'Carson City Storage',
    'city': 'Carson City',
    'state': 'NV',
    'address_line1': '123 Main St'  # Optional
}
facility_id = scraper.get_or_create_facility(facility_data)
```

---

## 2. Improved Bid13 Scraping

### Facility Name Parsing
The scraper now extracts facility names from the HTML:

**Before:**
```python
'facility_name': 'Bid13 Facility'  # Hardcoded
```

**After:**
```python
# Parses from: <span class="auc-owner">
#   <span class="field-content">Carson City Storage</span>
# </span>
facility_name = field_content.text.strip()
# Result: "Carson City Storage"
```

### Location Parsing
City and state are now extracted from the address field:

**Before:**
```python
'city': 'Unknown'
'state': 'CA'  # Hardcoded
```

**After:**
```python
# Address format: "Carson City, NV"
parts = address.split(',')
city = parts[0].strip()       # "Carson City"
state = parts[1][:2].upper()  # "NV"
```

---

## 3. Re-scraping Behavior (Already Working!)

### Question: "Will re-scraping create duplicates?"

**Answer: No!** The duplicate detection was already working correctly.

**How it works:**
1. Each auction has a unique `external_auction_id` (from the source website)
2. When saving, the scraper checks if `(external_auction_id, provider_id)` exists
3. If exists → **UPDATE** the record
4. If not exists → **INSERT** new record

**Code Reference:** `scrapers/base_scraper.py:84-122`

```python
# Check if auction exists
cursor.execute("""
    SELECT auction_id FROM auctions
    WHERE external_auction_id = %s AND provider_id = %s
""", (external_auction_id, provider_id))

if existing:
    # UPDATE existing auction
    cursor.execute("UPDATE auctions SET ...")
else:
    # INSERT new auction
    cursor.execute("INSERT INTO auctions ...")
```

**This means:**
- ✅ Safe to re-run scraper multiple times
- ✅ Existing auctions get updated with latest data
- ✅ Only new auctions create new records
- ✅ No duplicates!

---

## 4. Test Scrape Feature

### Problem
- Hard to test scrapers without polluting the database
- No way to preview what would be scraped before committing
- Difficult to debug scraper issues

### Solution
Added **dry-run mode** with visual preview in the admin portal.

### How to Use

#### Via Admin Portal:
1. Go to `/admin`
2. Find the provider you want to test
3. Click the **"Test"** button (purple)
4. View results in modal:
   - Summary: Found, Would Add, Would Update counts
   - Full table of auction details
   - **No data is saved to database**

#### Via API:
```bash
curl -X POST http://localhost:5000/api/providers/<provider_id>/scrape \
  -H "Content-Type: application/json" \
  -d '{"full_scrape": true, "dry_run": true}'
```

**Response includes:**
```json
{
  "success": true,
  "scrape_result": {
    "status": "success",
    "dry_run": true,
    "auctions_found": 15,
    "auctions_added": 12,
    "auctions_updated": 3,
    "auctions": [
      {
        "external_auction_id": "12345",
        "unit_number": "A101",
        "facility_name": "Carson City Storage",
        "city": "Carson City",
        "state": "NV",
        "unit_size": "10x10",
        "current_bid": 150,
        "closes_at": "2026-01-30T15:00:00",
        // ... full auction data
      }
    ]
  }
}
```

#### Via Command Line:
```bash
python scraper_cli.py run --provider-id <uuid> --dry-run
```

---

## 5. Database Migration

### Running the Migration

The facilities table migration has already been applied. If you need to run it on another database:

```bash
psql -d storage_auctions -f migrations/add_facilities_table.sql
```

### What it does:
1. Creates `facilities` table
2. Adds `facility_id` column to `auctions` table
3. Creates indexes for performance
4. Sets up foreign key constraints

### Backward Compatibility
- Existing auctions will have `facility_id = NULL` until re-scraped
- Denormalized fields (city, state, etc.) still work for old records
- No data loss

---

## 6. Testing Checklist

### To verify everything works:

1. **Test facility creation:**
   ```bash
   # Run a test scrape
   curl -X POST http://localhost:5000/api/providers/<id>/scrape \
     -d '{"dry_run": true}'

   # Check facility names are parsed correctly
   ```

2. **Test re-scraping:**
   ```bash
   # First scrape (creates records)
   python scraper_cli.py run --provider-id <uuid>

   # Second scrape (should update, not duplicate)
   python scraper_cli.py run --provider-id <uuid>

   # Verify no duplicates in database
   psql -d storage_auctions -c "
     SELECT external_auction_id, COUNT(*)
     FROM auctions
     GROUP BY external_auction_id
     HAVING COUNT(*) > 1;
   "
   # Should return 0 rows
   ```

3. **Test admin portal:**
   - Visit `/admin`
   - Click "Test" button
   - Verify modal shows auction preview
   - Check database has no new records after test

---

## 7. Code Reference

### Key Files Modified:

- **migrations/add_facilities_table.sql** - Database schema changes
- **scrapers/base_scraper.py** - Added `get_or_create_facility()` method
- **scrapers/bid13_scraper.py** - Facility name parsing, dry_run support
- **scrapers/storageauctions_scraper.py** - dry_run support
- **api_backend.py** - Added dry_run parameter to scrape endpoint
- **templates/admin.html** - Test scrape button and results modal

### API Endpoints:

```
POST /api/providers/<id>/scrape
Body: {
  "full_scrape": true,      // true = all auctions, false = updates only
  "dry_run": false          // true = don't save to DB, return preview
}
```

---

## 8. Next Steps

### Potential Enhancements:

1. **Address Geocoding**
   - Use facility addresses to get lat/long coordinates
   - Enable map-based auction search

2. **Facility Management UI**
   - Admin page to view/edit facilities
   - Manually add full addresses for facilities that don't have them
   - Merge duplicate facilities

3. **Scraper Scheduling**
   - Auto-run scrapers based on `scrape_frequency_hours`
   - Cron job or task scheduler integration

4. **Facility Photos**
   - Store facility photos in `facilities` table
   - Display in auction listings

5. **Historical Data**
   - Track facility address changes over time
   - Audit log for facility updates

---

## Questions?

- **Q: Will old auctions break?**
  - A: No, they'll have `facility_id = NULL` but still have denormalized location data

- **Q: Do I need to re-scrape everything?**
  - A: No, but re-scraping will populate `facility_id` and create facility records

- **Q: Can I test without affecting production?**
  - A: Yes! Use `dry_run: true` or the "Test" button in admin portal

- **Q: How do I update existing auction locations?**
  - A: Just re-run the scraper. It will UPDATE existing auctions with new facility info
