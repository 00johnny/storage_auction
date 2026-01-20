-- Storage Auction Platform Database Schema
-- Designed for PostgreSQL (can be adapted for MySQL/SQLite)

-- Enable UUID extension (PostgreSQL)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);

-- Indexes for users table
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_username ON users(username);

-- ============================================================================
-- PROVIDERS TABLE (Storage Companies)
-- ============================================================================
CREATE TABLE providers (
    provider_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    website VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    
    -- Location info
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL, -- Will expand beyond CA later
    zip_code VARCHAR(10) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- For scraping
    source_url VARCHAR(500), -- URL where we scrape this provider's auctions
    last_scraped_at TIMESTAMP,
    scrape_frequency_hours INT DEFAULT 24
);

-- Indexes for providers table
CREATE INDEX idx_providers_state ON providers(state);
CREATE INDEX idx_providers_city_state ON providers(city, state);
CREATE INDEX idx_providers_active ON providers(is_active);

-- ============================================================================
-- AUCTIONS TABLE
-- ============================================================================
CREATE TABLE auctions (
    auction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL,
    
    -- Unit details
    unit_number VARCHAR(50) NOT NULL,
    unit_size VARCHAR(20), -- e.g., "10x10", "10x20"
    unit_size_sqft INT,
    description TEXT,
    
    -- Location (denormalized for easier querying)
    facility_name VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Auction timing
    starts_at TIMESTAMP NOT NULL,
    closes_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP, -- Actual closing time (might differ from scheduled)
    
    -- Bidding info
    minimum_bid DECIMAL(10, 2) NOT NULL,
    current_bid DECIMAL(10, 2) DEFAULT 0,
    bid_increment DECIMAL(10, 2) DEFAULT 25.00,
    reserve_price DECIMAL(10, 2), -- Hidden reserve price (if any)
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, closed, cancelled, sold
    winner_user_id UUID, -- References users table
    winning_bid DECIMAL(10, 2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Scraping info
    source_url VARCHAR(500), -- Direct link to auction on provider site
    external_auction_id VARCHAR(100), -- Provider's auction ID
    last_scraped_at TIMESTAMP,
    
    -- Images (stored as JSON array of URLs)
    image_urls JSON,
    
    -- AI Image Analysis
    ai_description TEXT, -- AI-generated description of unit contents
    ai_analyzed_at TIMESTAMP, -- When AI analysis was performed
    ai_confidence_score DECIMAL(3, 2), -- Confidence score from AI (0.00 to 1.00)

    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE,
    FOREIGN KEY (winner_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Indexes for auctions table
CREATE INDEX idx_auctions_provider ON auctions(provider_id);
CREATE INDEX idx_auctions_closes_at ON auctions(closes_at);
CREATE INDEX idx_auctions_status ON auctions(status);
CREATE INDEX idx_auctions_state ON auctions(state);
CREATE INDEX idx_auctions_city_state ON auctions(city, state);
CREATE INDEX idx_auctions_location ON auctions(latitude, longitude);
CREATE INDEX idx_auctions_active_auctions ON auctions(status, closes_at); -- For finding open auctions

-- ============================================================================
-- AUCTION_TAGS TABLE
-- ============================================================================
CREATE TABLE tags (
    tag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tag_name VARCHAR(50) UNIQUE NOT NULL,
    tag_slug VARCHAR(50) UNIQUE NOT NULL, -- URL-friendly version
    description TEXT,
    color VARCHAR(7), -- Hex color code for UI display
    icon VARCHAR(50), -- Icon name for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INT DEFAULT 0 -- Denormalized count for performance
);

-- Indexes for tags table
CREATE INDEX idx_tags_tag_name ON tags(tag_name);
CREATE INDEX idx_tags_tag_slug ON tags(tag_slug);

-- Junction table for many-to-many relationship
CREATE TABLE auction_tags (
    auction_tag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    
    -- Source tracking
    source VARCHAR(20) DEFAULT 'manual', -- manual, ai_generated, user_suggested
    confidence DECIMAL(3, 2), -- For AI-generated tags
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by_user_id UUID, -- If manually added by a user
    
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (added_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL,

    UNIQUE (auction_id, tag_id)
);

-- Indexes for auction_tags table
CREATE INDEX idx_auction_tags_auction ON auction_tags(auction_id);
CREATE INDEX idx_auction_tags_tag ON auction_tags(tag_id);
CREATE INDEX idx_auction_tags_source ON auction_tags(source);

-- ============================================================================
-- BIDS TABLE
-- ============================================================================
CREATE TABLE bids (
    bid_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL,
    user_id UUID NOT NULL,
    
    -- Bid details
    bid_amount DECIMAL(10, 2) NOT NULL,
    bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status tracking
    is_winning BOOLEAN DEFAULT FALSE, -- Current winning bid
    is_outbid BOOLEAN DEFAULT FALSE, -- Has been outbid
    is_auto_bid BOOLEAN DEFAULT FALSE, -- If using proxy/auto-bidding
    max_auto_bid DECIMAL(10, 2), -- Max amount for auto-bidding
    
    -- Metadata
    ip_address VARCHAR(45), -- For fraud prevention
    user_agent TEXT,

    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for bids table
CREATE INDEX idx_bids_auction ON bids(auction_id);
CREATE INDEX idx_bids_user ON bids(user_id);
CREATE INDEX idx_bids_auction_user ON bids(auction_id, user_id);
CREATE INDEX idx_bids_bid_time ON bids(bid_time);
CREATE INDEX idx_bids_winning ON bids(is_winning);

-- ============================================================================
-- WATCHLIST TABLE (Users can watch auctions)
-- ============================================================================
CREATE TABLE watchlist (
    watchlist_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    auction_id UUID NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notify_before_closing BOOLEAN DEFAULT TRUE,
    notify_minutes_before INT DEFAULT 60,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE,

    UNIQUE (user_id, auction_id)
);

-- Indexes for watchlist table
CREATE INDEX idx_watchlist_user ON watchlist(user_id);
CREATE INDEX idx_watchlist_auction ON watchlist(auction_id);

-- ============================================================================
-- SCRAPE_LOGS TABLE (Track scraping activity)
-- ============================================================================
CREATE TABLE scrape_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID,
    scrape_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scrape_completed_at TIMESTAMP,
    status VARCHAR(20), -- success, failed, partial
    auctions_found INT DEFAULT 0,
    auctions_added INT DEFAULT 0,
    auctions_updated INT DEFAULT 0,
    error_message TEXT,

    FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE
);

-- Indexes for scrape_logs table
CREATE INDEX idx_scrape_logs_provider ON scrape_logs(provider_id);
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status);
CREATE INDEX idx_scrape_logs_started_at ON scrape_logs(scrape_started_at);

-- ============================================================================
-- NOTIFICATIONS TABLE (User notifications)
-- ============================================================================
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    auction_id UUID,
    
    type VARCHAR(50) NOT NULL, -- outbid, auction_ending, auction_won, auction_lost
    title VARCHAR(255) NOT NULL,
    message TEXT,

    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (auction_id) REFERENCES auctions(auction_id) ON DELETE CASCADE
);

-- Indexes for notifications table
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- Active auctions with current bid counts and tags
CREATE VIEW active_auctions_summary AS
SELECT 
    a.*,
    p.name as provider_name,
    COUNT(DISTINCT b.user_id) as unique_bidders,
    COUNT(b.bid_id) as total_bids,
    MAX(b.bid_amount) as highest_bid,
    STRING_AGG(t.tag_name, ', ') as tags
FROM auctions a
LEFT JOIN providers p ON a.provider_id = p.provider_id
LEFT JOIN bids b ON a.auction_id = b.auction_id
LEFT JOIN auction_tags at ON a.auction_id = at.auction_id
LEFT JOIN tags t ON at.tag_id = t.tag_id
WHERE a.status = 'active' 
    AND a.closes_at > CURRENT_TIMESTAMP
GROUP BY a.auction_id, p.name;

-- User bidding history
CREATE VIEW user_bid_history AS
SELECT 
    u.user_id,
    u.username,
    u.email,
    b.bid_id,
    b.auction_id,
    b.bid_amount,
    b.bid_time,
    b.is_winning,
    a.unit_number,
    a.city,
    a.state,
    p.name as provider_name
FROM users u
JOIN bids b ON u.user_id = b.user_id
JOIN auctions a ON b.auction_id = a.auction_id
JOIN providers p ON a.provider_id = p.provider_id;

-- Popular tags view
CREATE VIEW popular_tags AS
SELECT 
    t.tag_id,
    t.tag_name,
    t.tag_slug,
    COUNT(at.auction_id) as auction_count,
    AVG(at.confidence) as avg_confidence
FROM tags t
LEFT JOIN auction_tags at ON t.tag_id = at.tag_id
GROUP BY t.tag_id, t.tag_name, t.tag_slug
ORDER BY auction_count DESC;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_providers_timestamp
    BEFORE UPDATE ON providers
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_auctions_timestamp
    BEFORE UPDATE ON auctions
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample providers
INSERT INTO providers (name, city, state, zip_code, website, source_url) VALUES
('StorageMart Sacramento', 'Sacramento', 'CA', '95814', 'https://www.storagemart.com', 'https://www.storagemart.com/auctions'),
('Public Storage Los Angeles', 'Los Angeles', 'CA', '90012', 'https://www.publicstorage.com', 'https://www.publicstorage.com/auctions'),
('Extra Space Storage San Diego', 'San Diego', 'CA', '92101', 'https://www.extraspace.com', 'https://www.extraspace.com/auctions'),
('CubeSmart San Francisco', 'San Francisco', 'CA', '94102', 'https://www.cubesmart.com', 'https://www.cubesmart.com/auctions'),
('Life Storage Fresno', 'Fresno', 'CA', '93721', 'https://www.lifestorage.com', 'https://www.lifestorage.com/auctions');

-- Insert sample tags
INSERT INTO tags (tag_name, tag_slug, description, color) VALUES
('furniture', 'furniture', 'Contains furniture items like chairs, tables, dressers', '#3B82F6'),
('electronics', 'electronics', 'Contains electronic devices and equipment', '#8B5CF6'),
('tools', 'tools', 'Contains tools and equipment', '#F59E0B'),
('boxes', 'boxes', 'Contains many boxes or storage containers', '#6B7280'),
('appliances', 'appliances', 'Contains appliances like refrigerators, washers, etc.', '#10B981'),
('sports', 'sports', 'Contains sporting goods and equipment', '#EF4444'),
('office', 'office', 'Contains office furniture and equipment', '#06B6D4'),
('household', 'household', 'General household items', '#84CC16'),
('outdoor', 'outdoor', 'Contains outdoor equipment and gear', '#14B8A6'),
('premium', 'premium', 'High-value or well-maintained items', '#F97316'),
('computers', 'computers', 'Contains computers and related equipment', '#8B5CF6'),
('miscellaneous', 'miscellaneous', 'Mixed or varied contents', '#6B7280');

-- Sample query to verify
-- SELECT * FROM providers;
-- SELECT * FROM tags;
