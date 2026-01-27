# Storage Auction Platform - Feature Implementation Plan

This document tracks the implementation of the requested features from the latest session.

## ✅ COMPLETED (Commit: b43f1d1)

### 1. User Authentication System Foundation
- [x] Created users table with role-based access (admin, power, regular)
- [x] Added bcrypt password hashing
- [x] Installed Flask-Login for session management
- [x] Created User model with role checking
- [x] Added authentication API endpoints:
  - POST `/api/auth/login`
  - POST `/api/auth/logout`
  - GET `/api/auth/me`
  - GET `/api/auth/check`
- [x] Track last_login_at and login_count
- [x] Created default users:
  - `admin` / `admin123` (admin role)
  - `testuser` / `test123` (regular role)

**Status:** Backend complete, needs frontend

---

## 🚧 IN PROGRESS (13 Features Remaining)

### 2. Login Page & User Interface
**Status:** Not started
**Priority:** HIGH (required for authentication to work)
**Tasks:**
- [ ] Create `/templates/login.html` page
- [ ] Add login form with username/password
- [ ] Add registration form for new users
- [ ] Add logout button to main nav
- [ ] Display current user info in header
- [ ] Redirect to login if not authenticated
- [ ] Add "Remember me" checkbox

---

### 3. User Management in Admin Portal
**Status:** Not started
**Priority:** HIGH (core admin feature)
**Tasks:**
- [ ] Add "Users" tab to admin portal
- [ ] Create users table showing:
  - Username, Email, Role
  - Last Login, Login Count
  - Active status
- [ ] Add "Edit User" modal with fields:
  - Username, Email
  - Role (admin/power/regular dropdown)
  - Active status toggle
  - Change password
- [ ] Add "Create User" button
- [ ] Add user deletion (with confirmation)
- [ ] Add API endpoints:
  - GET `/api/users` - List all users
  - POST `/api/users` - Create user
  - PUT `/api/users/<id>` - Update user
  - DELETE `/api/users/<id>` - Delete user

---

### 4. Fix Auction Titles (Remove "Unit Unit" Duplication)
**Status:** Not started
**Priority:** HIGH (user-facing bug)
**Current:** "Unit Unit 345"
**Desired:** "Carson City Storage - Unit 345"
**Tasks:**
- [ ] Update scraper to parse unit number without "Unit" prefix
- [ ] Update frontend to display: `{facility_name} - {unit_number}`
- [ ] Apply to both listing page and detail page
- [ ] Update existing auction records (migration or re-scrape)

---

### 5. Save & Display Auction Source URL
**Status:** Not started
**Priority:** HIGH (important for users)
**Tasks:**
- [ ] Verify `source_url` is already in auctions table (it is!)
- [ ] Add "View on Bid13" link button on detail page
- [ ] Style as external link with icon
- [ ] Open in new tab (`target="_blank"`)

---

### 6. Remove Bidding UI from Detail Page
**Status:** Not started
**Priority:** HIGH (remove confusing UI)
**Tasks:**
- [ ] Remove "Place Bid" button
- [ ] Remove bid amount input field
- [ ] Remove bid history section
- [ ] Keep current bid display (read-only)
- [ ] Add note: "Bidding opens on {source_site}"

---

### 7. Make Auction Titles Clickable on Listing Page
**Status:** Not started
**Priority:** MEDIUM
**Tasks:**
- [ ] Wrap auction title in `<a>` tag or add `onClick`
- [ ] Link to `/auction/{auction_id}` (detail page)
- [ ] Add hover effect (underline, color change)
- [ ] Ensure card is still clickable elsewhere

---

### 8. Remove Eyeball Icon from Detail Link
**Status:** Not started
**Priority:** LOW (cosmetic)
**Tasks:**
- [ ] Find Eye icon component in `storage-auctions-enhanced.jsx`
- [ ] Remove from "View Details" button
- [ ] Keep button text only

---

### 9. Provider-to-Facilities Link
**Status:** Not started
**Priority:** MEDIUM
**Tasks:**
- [ ] Add "View Facilities" button/link on provider row in admin
- [ ] Filter facilities table by `provider_id`
- [ ] Show count badge: "5 facilities"
- [ ] Click to jump to Facilities tab with filter applied

---

### 10. Clickable Auction Count to Filter by Provider
**Status:** Not started
**Priority:** MEDIUM
**Tasks:**
- [ ] Make "Active Auctions" count clickable in providers table
- [ ] On click, redirect to main page with provider filter
- [ ] Update frontend to accept `?provider={name}` URL parameter
- [ ] Apply filter automatically when page loads

---

### 11. Facility Deletion Feature (Fix Duplicates)
**Status:** Not started
**Priority:** MEDIUM (needed to clean up duplicates)
**Tasks:**
- [ ] Add DELETE endpoint: `/api/facilities/<id>`
- [ ] Add "Delete" button to facilities table in admin
- [ ] Show confirmation dialog with warning:
  - "This facility has X active auctions"
  - "Auctions will keep denormalized location data"
  - "Are you sure?"
- [ ] Prevent deletion if facility has auctions (or cascade?)
- [ ] Add "Merge Facilities" feature (optional, complex)

---

### 12. Admin-Only Re-Fetch Button on Auction Detail
**Status:** Not started
**Priority:** LOW (admin utility)
**Tasks:**
- [ ] Add "Admin Tools" section at bottom of detail page
- [ ] Show only if `user.role === 'admin'`
- [ ] Add "Re-fetch from Source" button
- [ ] On click, call `/api/auctions/<id>/refetch` endpoint
- [ ] Endpoint re-scrapes specific auction by source_url
- [ ] Show loading spinner during fetch
- [ ] Show success/error message
- [ ] Refresh page data after refetch

---

### 13. Add Fullness Rating Field (1-5 stars)
**Status:** Not started
**Priority:** LOW (future AI feature)
**Tasks:**
- [ ] Add `fullness_rating` column to auctions table:
  ```sql
  ALTER TABLE auctions ADD COLUMN fullness_rating INT CHECK (fullness_rating BETWEEN 1 AND 5);
  ```
- [ ] Add fullness rating display on detail page:
  - Show 1-5 stars (⭐⭐⭐⭐⭐)
  - Label: "Estimated Fullness"
  - Tooltip: "Based on AI image analysis"
- [ ] Add placeholder logic (set to NULL initially)
- [ ] Note in comments: "TODO: Integrate AI analysis"

---

### 14. Database Migration: Add Fullness Rating
**Status:** Not started
**File:** `migrations/add_fullness_rating.sql`
```sql
ALTER TABLE auctions ADD COLUMN fullness_rating INT;
ALTER TABLE auctions ADD CONSTRAINT check_fullness_rating CHECK (fullness_rating IS NULL OR (fullness_rating >= 1 AND fullness_rating <= 5));
COMMENT ON COLUMN auctions.fullness_rating IS 'AI-estimated fullness: 1 (nearly empty) to 5 (very full)';
```

---

## 📊 Implementation Progress

| Category | Completed | Total | Progress |
|----------|-----------|-------|----------|
| Authentication | 1 | 3 | 33% |
| UI Improvements | 0 | 5 | 0% |
| Admin Features | 1 | 4 | 25% |
| Provider/Facility | 0 | 2 | 0% |
| AI/Future | 0 | 1 | 0% |
| **TOTAL** | **2** | **15** | **13%** |

---

## 🎯 Recommended Implementation Order

### Phase 1: Authentication (HIGH PRIORITY)
1. Login page HTML/CSS/JS
2. User management in admin portal
3. Protected routes middleware

### Phase 2: Quick Wins (HIGH PRIORITY, FAST)
4. Fix auction title formatting
5. Add source URL link
6. Remove bidding UI
7. Remove eyeball icon
8. Make titles clickable

### Phase 3: Admin Features (MEDIUM PRIORITY)
9. Provider-to-facilities link
10. Clickable auction count
11. Facility deletion

### Phase 4: Advanced Features (LOW PRIORITY)
12. Admin re-fetch button
13. Fullness rating field

---

## 🔑 Default Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Role: `admin`

**Test User:**
- Username: `testuser`
- Password: `test123`
- Role: `regular`

⚠️ **IMPORTANT:** Change the admin password immediately in production!

---

## 📝 Notes

- All API endpoints are RESTful and return JSON
- Role hierarchy: `admin` > `power` > `regular`
- Admin can do everything
- Power users can do most things (TBD which features)
- Regular users can only view (no edit/delete)
- Sessions last 7 days with "remember me"
- Passwords are hashed with bcrypt (cost factor: 12)

---

## 🚀 Next Steps

**Option A:** Continue implementing all features in order
**Option B:** Focus on specific high-priority features first
**Option C:** Implement Phase 1 (auth) completely, then Phase 2 (quick wins)

**Recommended:** Option C - Complete authentication, then tackle the quick UI fixes that will immediately improve user experience.
