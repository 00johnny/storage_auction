-- Migration: Add geocoding cache table to store geocoded locations
-- This dramatically improves performance by caching API results
-- and reduces load on the free Nominatim geocoding service

-- ============================================================================
-- GEOCODED LOCATIONS CACHE TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS geocoded_locations (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Location identification
    location_type VARCHAR(20) NOT NULL, -- 'zipcode' or 'city_state'
    location_key VARCHAR(255) NOT NULL, -- e.g., '95672' or 'Sacramento,CA'

    -- Geocoded coordinates
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,

    -- Cache metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hit_count INTEGER DEFAULT 0, -- Track how often this cache entry is used

    -- Ensure unique cache entries
    UNIQUE(location_type, location_key)
);

-- Indexes for fast lookups
CREATE INDEX idx_geocode_cache_lookup ON geocoded_locations(location_type, location_key);
CREATE INDEX idx_geocode_cache_created ON geocoded_locations(created_at);

-- Migration notes:
-- - This cache persists across server restarts
-- - Nominatim has a 1-second rate limit, so caching is critical for performance
-- - location_key format: zipcode='95672', city_state='Sacramento,CA'
-- - hit_count tracks cache efficiency for monitoring
