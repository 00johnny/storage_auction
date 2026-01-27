-- Migration: Add fullness rating field for AI analysis
-- This adds a 1-5 star rating for how full a storage unit appears to be

ALTER TABLE auctions ADD COLUMN fullness_rating INT;

-- Add constraint to ensure rating is between 1-5 or NULL
ALTER TABLE auctions ADD CONSTRAINT check_fullness_rating
    CHECK (fullness_rating IS NULL OR (fullness_rating >= 1 AND fullness_rating <= 5));

-- Add comment explaining the field
COMMENT ON COLUMN auctions.fullness_rating IS 'AI-estimated fullness: 1 (nearly empty) to 5 (very full). NULL = not analyzed yet.';

-- Add index for filtering by fullness
CREATE INDEX idx_auctions_fullness ON auctions(fullness_rating) WHERE fullness_rating IS NOT NULL;
