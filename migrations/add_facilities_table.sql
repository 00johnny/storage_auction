-- Migration: Add facilities table to store physical storage locations
-- This allows multiple auctions to reference the same facility
-- and maintain consistent address information

-- ============================================================================
-- FACILITIES TABLE
-- ============================================================================
CREATE TABLE facilities (
    facility_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL,

    -- Facility identification
    facility_name VARCHAR(255) NOT NULL,

    -- Full address information
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10),

    -- Geolocation
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),

    -- Contact info
    phone VARCHAR(20),
    email VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE,

    -- Ensure unique facility per provider by name+city+state combination
    UNIQUE(provider_id, facility_name, city, state)
);

-- Indexes for facilities table
CREATE INDEX idx_facilities_provider ON facilities(provider_id);
CREATE INDEX idx_facilities_city_state ON facilities(city, state);
CREATE INDEX idx_facilities_location ON facilities(latitude, longitude);
CREATE INDEX idx_facilities_lookup ON facilities(provider_id, facility_name, city, state);

-- ============================================================================
-- UPDATE AUCTIONS TABLE
-- ============================================================================
-- Add facility_id foreign key to auctions table
ALTER TABLE auctions ADD COLUMN facility_id UUID;
ALTER TABLE auctions ADD CONSTRAINT fk_auctions_facility
    FOREIGN KEY (facility_id) REFERENCES facilities(facility_id) ON DELETE SET NULL;

-- Create index for facility lookups
CREATE INDEX idx_auctions_facility ON auctions(facility_id);

-- Migration notes:
-- - The auctions table still keeps denormalized location data (city, state, etc.)
--   for backward compatibility and faster queries
-- - New scraper code will populate both facility_id and denormalized fields
-- - Existing auctions will have NULL facility_id until re-scraped
