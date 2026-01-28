-- Migration: Add users table and authentication system
-- This adds user accounts with role-based permissions

-- ============================================================================
-- USERS TABLE (Enhanced with authentication)
-- ============================================================================

-- Drop and recreate users table with proper authentication fields
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- User info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),

    -- Role-based permissions
    role VARCHAR(20) DEFAULT 'regular' CHECK (role IN ('admin', 'power', 'regular')),

    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    login_count INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Create default admin user (password: admin123)
-- NOTE: Change this password immediately in production!
INSERT INTO users (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    email_verified
) VALUES (
    'admin',
    'admin@localhost',
    -- Password: admin123 (bcrypt hash)
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eplkvZJBbJAa',
    'Admin',
    'User',
    'admin',
    TRUE,
    TRUE
);

-- Create a regular test user (password: test123)
INSERT INTO users (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    email_verified
) VALUES (
    'testuser',
    'test@localhost',
    -- Password: test123 (bcrypt hash)
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Test',
    'User',
    'regular',
    TRUE,
    TRUE
);

COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON COLUMN users.role IS 'User role: admin (full access), power (elevated), regular (basic)';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp of most recent login';
COMMENT ON COLUMN users.login_count IS 'Total number of successful logins';
