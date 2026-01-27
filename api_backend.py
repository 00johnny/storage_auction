"""
Storage Auction Platform - REST API Backend

A Flask-based REST API for the storage auction platform.

Dependencies:
    pip install flask flask-cors psycopg2-binary python-dotenv --break-system-packages

Environment Variables (create .env file):
    DATABASE_URL=postgresql://user:password@localhost:5432/storage_auctions
    SECRET_KEY=your-secret-key
    HUGGINGFACE_API_TOKEN=your-token
"""

from flask import Flask, jsonify, request, send_from_directory, render_template, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv
import bcrypt

# Load environment variables from .env file
load_dotenv()

# Import our helper modules
# from image_analysis_geocoding import GeocodeService, ImageAnalysisService


app = Flask(__name__, static_folder='.')
CORS(app, supports_credentials=True)  # Enable CORS with credentials for sessions

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, email, role, is_active=True):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self._is_active = is_active

    @property
    def is_active(self):
        """Override UserMixin's is_active property"""
        return self._is_active

    def has_role(self, role):
        """Check if user has specific role"""
        if role == 'admin':
            return self.role == 'admin'
        elif role == 'power':
            return self.role in ['admin', 'power']
        else:
            return True  # Everyone has 'regular' access

@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, email, role, is_active
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return User(
                user_id=str(user_data['user_id']),
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                is_active=user_data['is_active']
            )
    except Exception as e:
        print(f"Error loading user: {e}")
    return None


# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection():
    """Create database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# ============================================================================
# Frontend Routes
# ============================================================================

@app.route('/')
def serve_frontend():
    """Serve the React frontend with injected configuration"""
    return render_template('index.html', api_base_url=API_BASE_URL)

@app.route('/admin')
@app.route('/admin/')
def serve_admin():
    """Serve the admin portal"""
    return render_template('admin.html', api_base_url=API_BASE_URL)

@app.route('/login')
def login_page():
    """Serve the login page"""
    return render_template('login.html', api_base_url=API_BASE_URL)


# ============================================================================
# API Routes - Authentication
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user by username or email
        cursor.execute("""
            SELECT user_id, username, email, password_hash, role, is_active
            FROM users
            WHERE (username = %s OR email = %s) AND is_active = TRUE
        """, (username, username))

        user_data = cursor.fetchone()

        if not user_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401

        # Update last login
        cursor.execute("""
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP,
                login_count = login_count + 1
            WHERE user_id = %s
        """, (user_data['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()

        # Create user object and login
        user = User(
            user_id=str(user_data['user_id']),
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )
        login_user(user, remember=True)

        return jsonify({
            'success': True,
            'user': {
                'user_id': str(user_data['user_id']),
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role']
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint"""
    logout_user()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged in user"""
    return jsonify({
        'success': True,
        'user': {
            'user_id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role
        }
    })

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'user_id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role
            }
        })
    else:
        return jsonify({
            'success': True,
            'authenticated': False
        })


# ============================================================================
# API Routes - Auctions
# ============================================================================

@app.route('/api/auctions', methods=['GET'])
def get_auctions():
    """
    Get all active auctions with optional filtering
    
    Query Parameters:
        state: Filter by state (default: CA)
        city: Filter by city
        tags: Comma-separated tag names
        search: Search term for description/title
        sort: Sort by (closing-soon, highest-bid, lowest-bid)
        limit: Max results (default: 50)
        offset: Pagination offset (default: 0)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT 
                a.*,
                p.name as provider_name,
                STRING_AGG(t.tag_name, ',') as tags,
                COUNT(DISTINCT b.user_id) as unique_bidders,
                COUNT(b.bid_id) as total_bids
            FROM auctions a
            LEFT JOIN providers p ON a.provider_id = p.provider_id
            LEFT JOIN auction_tags at ON a.auction_id = at.auction_id
            LEFT JOIN tags t ON at.tag_id = t.tag_id
            LEFT JOIN bids b ON a.auction_id = b.auction_id
            WHERE a.status = 'active' AND a.closes_at > CURRENT_TIMESTAMP
        """
        
        params = []
        
        # State filter
        state = request.args.get('state', 'CA')
        query += " AND a.state = %s"
        params.append(state)
        
        # City filter
        city = request.args.get('city')
        if city:
            query += " AND a.city = %s"
            params.append(city)
        
        # Search filter
        search = request.args.get('search')
        if search:
            query += " AND (a.description ILIKE %s OR a.unit_number ILIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        # Group by
        query += """
            GROUP BY a.auction_id, p.name
        """
        
        # Tag filter (after GROUP BY)
        tags = request.args.get('tags')
        if tags:
            tag_list = tags.split(',')
            query += f" HAVING STRING_AGG(t.tag_name, ',') LIKE %s"
            params.append(f"%{tag_list[0]}%")  # Simplified - improve for multiple tags
        
        # Sorting
        sort = request.args.get('sort', 'closing-soon')
        if sort == 'highest-bid':
            query += " ORDER BY a.current_bid DESC"
        elif sort == 'lowest-bid':
            query += " ORDER BY a.current_bid ASC"
        else:  # closing-soon
            query += " ORDER BY a.closes_at ASC"
        
        # Pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        auctions = cursor.fetchall()
        
        # Convert to list of dicts and process
        result = []
        for auction in auctions:
            auction_dict = dict(auction)
            
            # Parse JSON fields
            if auction_dict.get('image_urls'):
                auction_dict['image_urls'] = json.loads(auction_dict['image_urls'])
            
            # Convert tags string to list
            if auction_dict.get('tags'):
                auction_dict['tags'] = auction_dict['tags'].split(',')
            else:
                auction_dict['tags'] = []
            
            # Convert datetime to ISO string
            for field in ['closes_at', 'starts_at', 'created_at']:
                if auction_dict.get(field):
                    auction_dict[field] = auction_dict[field].isoformat()
            
            result.append(auction_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(result),
            'auctions': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auctions/<auction_id>', methods=['GET'])
def get_auction(auction_id):
    """Get detailed information for a specific auction"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get auction details
        cursor.execute("""
            SELECT 
                a.*,
                p.name as provider_name,
                p.phone as provider_phone,
                p.website as provider_website
            FROM auctions a
            LEFT JOIN providers p ON a.provider_id = p.provider_id
            WHERE a.auction_id = %s
        """, (auction_id,))
        
        auction = cursor.fetchone()
        
        if not auction:
            return jsonify({
                'success': False,
                'error': 'Auction not found'
            }), 404
        
        auction_dict = dict(auction)
        
        # Get tags
        cursor.execute("""
            SELECT t.tag_name, t.color
            FROM auction_tags at
            JOIN tags t ON at.tag_id = t.tag_id
            WHERE at.auction_id = %s
        """, (auction_id,))
        
        tags = [dict(row) for row in cursor.fetchall()]
        auction_dict['tags'] = tags
        
        # Get bid history
        cursor.execute("""
            SELECT 
                b.bid_amount,
                b.bid_time,
                u.username,
                b.is_winning
            FROM bids b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE b.auction_id = %s
            ORDER BY b.bid_time DESC
            LIMIT 20
        """, (auction_id,))
        
        bid_history = [dict(row) for row in cursor.fetchall()]
        for bid in bid_history:
            if bid.get('bid_time'):
                bid['bid_time'] = bid['bid_time'].isoformat()
        
        auction_dict['bid_history'] = bid_history
        
        # Parse JSON and convert dates
        if auction_dict.get('image_urls'):
            auction_dict['image_urls'] = json.loads(auction_dict['image_urls'])
        
        for field in ['closes_at', 'starts_at', 'created_at']:
            if auction_dict.get(field):
                auction_dict[field] = auction_dict[field].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'auction': auction_dict
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auctions/<auction_id>/refetch', methods=['POST'])
@login_required
def refetch_auction(auction_id):
    """
    Re-fetch auction from source (admin only)

    This endpoint triggers a re-scrape of a specific auction from its original source.
    Only accessible to admin users.
    """
    if not current_user.has_role('admin'):
        return jsonify({
            'success': False,
            'error': 'Unauthorized. Admin access required.'
        }), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get auction and provider details
        cursor.execute("""
            SELECT
                a.source_url,
                a.external_auction_id,
                a.provider_id,
                p.name as provider_name,
                p.source_url as provider_url
            FROM auctions a
            JOIN providers p ON a.provider_id = p.provider_id
            WHERE a.auction_id = %s
        """, (auction_id,))

        auction = cursor.fetchone()
        cursor.close()
        conn.close()

        if not auction:
            return jsonify({
                'success': False,
                'error': 'Auction not found'
            }), 404

        # Determine which scraper to use based on provider URL
        provider_url = auction['provider_url']
        provider_id = str(auction['provider_id'])

        if 'bid13.com' in provider_url:
            from scrapers.bid13_scraper import Bid13Scraper
            scraper = Bid13Scraper(provider_id, provider_url)
        elif 'storageauctions.com' in provider_url:
            from scrapers.storageauctions_scraper import StorageAuctionsScraper
            scraper = StorageAuctionsScraper(provider_id)
        else:
            return jsonify({
                'success': False,
                'error': f'No scraper available for provider: {auction["provider_name"]}'
            }), 400

        # Run a full scrape (this will update existing auctions including this one)
        # Note: We run a full scrape because individual auction scraping isn't implemented yet
        result = scraper.run_scraper(full_scrape=True, dry_run=False)

        return jsonify({
            'success': True,
            'message': f'Re-fetched auctions from {auction["provider_name"]}',
            'result': {
                'auctions_found': result.get('auctions_found', 0),
                'auctions_added': result.get('auctions_added', 0),
                'auctions_updated': result.get('auctions_updated', 0)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error re-fetching auction: {str(e)}'
        }), 500


# ============================================================================
# API Routes - Bids
# ============================================================================

@app.route('/api/auctions/<auction_id>/bids', methods=['POST'])
def place_bid(auction_id):
    """
    Place a bid on an auction
    
    Request Body:
        user_id: User ID (in production, use auth token)
        bid_amount: Bid amount
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bid_amount = float(data.get('bid_amount'))
        
        if not user_id or not bid_amount:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get auction details
        cursor.execute("""
            SELECT current_bid, bid_increment, closes_at, status
            FROM auctions
            WHERE auction_id = %s
        """, (auction_id,))
        
        auction = cursor.fetchone()
        
        if not auction:
            return jsonify({
                'success': False,
                'error': 'Auction not found'
            }), 404
        
        # Validate bid
        min_bid = auction['current_bid'] + auction['bid_increment']
        if bid_amount < min_bid:
            return jsonify({
                'success': False,
                'error': f'Bid must be at least ${min_bid}'
            }), 400
        
        if auction['status'] != 'active':
            return jsonify({
                'success': False,
                'error': 'Auction is not active'
            }), 400
        
        if datetime.now() > auction['closes_at']:
            return jsonify({
                'success': False,
                'error': 'Auction has closed'
            }), 400
        
        # Mark previous winning bids as outbid
        cursor.execute("""
            UPDATE bids
            SET is_winning = FALSE, is_outbid = TRUE
            WHERE auction_id = %s AND is_winning = TRUE
        """, (auction_id,))
        
        # Insert new bid
        cursor.execute("""
            INSERT INTO bids (auction_id, user_id, bid_amount, is_winning)
            VALUES (%s, %s, %s, TRUE)
            RETURNING bid_id, bid_time
        """, (auction_id, user_id, bid_amount))
        
        bid = cursor.fetchone()
        
        # Update auction current_bid
        cursor.execute("""
            UPDATE auctions
            SET current_bid = %s, updated_at = CURRENT_TIMESTAMP
            WHERE auction_id = %s
        """, (bid_amount, auction_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'bid': {
                'bid_id': bid['bid_id'],
                'bid_amount': bid_amount,
                'bid_time': bid['bid_time'].isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API Routes - Tags
# ============================================================================

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all available tags"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, COUNT(at.auction_id) as auction_count
            FROM tags t
            LEFT JOIN auction_tags at ON t.tag_id = at.tag_id
            GROUP BY t.tag_id
            ORDER BY auction_count DESC
        """)
        
        tags = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'tags': tags
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API Routes - Search & Filter
# ============================================================================

@app.route('/api/search', methods=['GET'])
def search_auctions():
    """Advanced search with multiple filters"""
    try:
        search_term = request.args.get('q', '')
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        city = request.args.get('city')
        min_bid = request.args.get('min_bid', type=float)
        max_bid = request.args.get('max_bid', type=float)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT a.*, p.name as provider_name
            FROM auctions a
            LEFT JOIN providers p ON a.provider_id = p.provider_id
            LEFT JOIN auction_tags at ON a.auction_id = at.auction_id
            LEFT JOIN tags t ON at.tag_id = t.tag_id
            WHERE a.status = 'active'
        """
        
        params = []
        
        if search_term:
            query += " AND (a.description ILIKE %s OR a.unit_number ILIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        if tags:
            placeholders = ','.join(['%s'] * len(tags))
            query += f" AND t.tag_name IN ({placeholders})"
            params.extend(tags)
        
        if city:
            query += " AND a.city = %s"
            params.append(city)
        
        if min_bid is not None:
            query += " AND a.current_bid >= %s"
            params.append(min_bid)
        
        if max_bid is not None:
            query += " AND a.current_bid <= %s"
            params.append(max_bid)
        
        query += " ORDER BY a.closes_at ASC LIMIT 100"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API Routes - Providers (Full CRUD)
# ============================================================================

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get all storage providers with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add filtering options
        state = request.args.get('state')
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        query = """
            SELECT p.*,
                   COUNT(DISTINCT a.auction_id) as active_auctions,
                   COUNT(DISTINCT f.facility_id) as facility_count
            FROM providers p
            LEFT JOIN auctions a ON p.provider_id = a.provider_id AND a.status = 'active'
            LEFT JOIN facilities f ON p.provider_id = f.provider_id
            WHERE 1=1
        """
        params = []

        if active_only:
            query += " AND p.is_active = TRUE"

        if state:
            query += " AND p.state = %s"
            params.append(state)

        query += " GROUP BY p.provider_id ORDER BY p.name"

        cursor.execute(query, params)
        providers = [dict(row) for row in cursor.fetchall()]

        # Convert datetime fields to ISO strings
        for provider in providers:
            for field in ['created_at', 'updated_at', 'last_scraped_at']:
                if provider.get(field):
                    provider[field] = provider[field].isoformat()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'providers': providers
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers/<provider_id>', methods=['GET'])
def get_provider(provider_id):
    """Get a single provider by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*,
                   COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.auction_id END) as active_auctions,
                   COUNT(DISTINCT a.auction_id) as total_auctions,
                   MAX(sl.scrape_started_at) as last_scrape_time,
                   (SELECT status FROM scrape_logs WHERE provider_id = p.provider_id
                    ORDER BY scrape_started_at DESC LIMIT 1) as last_scrape_status
            FROM providers p
            LEFT JOIN auctions a ON p.provider_id = a.provider_id
            LEFT JOIN scrape_logs sl ON p.provider_id = sl.provider_id
            WHERE p.provider_id = %s
            GROUP BY p.provider_id
        """, (provider_id,))

        provider = cursor.fetchone()

        if not provider:
            return jsonify({
                'success': False,
                'error': 'Provider not found'
            }), 404

        provider_dict = dict(provider)

        # Convert datetime fields
        for field in ['created_at', 'updated_at', 'last_scraped_at', 'last_scrape_time']:
            if provider_dict.get(field):
                provider_dict[field] = provider_dict[field].isoformat()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'provider': provider_dict
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers', methods=['POST'])
def create_provider():
    """Create a new provider"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'city', 'state', 'zip_code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO providers (
                name,
                website,
                phone,
                email,
                address_line1,
                address_line2,
                city,
                state,
                zip_code,
                source_url,
                scrape_frequency_hours,
                is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING provider_id
        """, (
            data.get('name'),
            data.get('website'),
            data.get('phone'),
            data.get('email'),
            data.get('address_line1'),
            data.get('address_line2'),
            data.get('city'),
            data.get('state'),
            data.get('zip_code'),
            data.get('source_url'),
            data.get('scrape_frequency_hours', 24),
            data.get('is_active', True)
        ))

        provider_id = cursor.fetchone()['provider_id']

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'provider_id': provider_id,
            'message': 'Provider created successfully'
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    """Update an existing provider"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if provider exists
        cursor.execute("SELECT provider_id FROM providers WHERE provider_id = %s", (provider_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Provider not found'
            }), 404

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        allowed_fields = [
            'name', 'website', 'phone', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'zip_code', 'source_url', 'scrape_frequency_hours', 'is_active'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if not update_fields:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400

        # Add updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(provider_id)

        query = f"UPDATE providers SET {', '.join(update_fields)} WHERE provider_id = %s"
        cursor.execute(query, params)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Provider updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers/<provider_id>', methods=['DELETE'])
def delete_provider(provider_id):
    """Delete a provider (soft delete by setting is_active to false)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if provider exists
        cursor.execute("SELECT provider_id FROM providers WHERE provider_id = %s", (provider_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Provider not found'
            }), 404

        # Soft delete - set is_active to false
        cursor.execute("""
            UPDATE providers
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE provider_id = %s
        """, (provider_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Provider deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers/<provider_id>/scrape', methods=['POST'])
def trigger_scrape(provider_id):
    """Manually trigger a scrape for a specific provider"""
    try:
        data = request.get_json() or {}
        full_scrape = data.get('full_scrape', True)
        dry_run = data.get('dry_run', False)  # Add dry_run support

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get provider details
        cursor.execute("""
            SELECT name, source_url FROM providers
            WHERE provider_id = %s AND is_active = TRUE
        """, (provider_id,))

        provider = cursor.fetchone()
        cursor.close()
        conn.close()

        if not provider:
            return jsonify({
                'success': False,
                'error': 'Provider not found or inactive'
            }), 404

        if not provider['source_url']:
            return jsonify({
                'success': False,
                'error': 'Provider has no source_url configured'
            }), 400

        # Import scrapers here to avoid circular imports
        from scrapers import Bid13Scraper, StorageAuctionsScraper

        # Determine which scraper to use based on provider or URL
        # This is a simple example - you might want to store scraper_type in the database
        if 'bid13.com' in provider['source_url']:
            scraper = Bid13Scraper(provider_id, provider['source_url'])
        elif 'storageauctions.com' in provider['source_url']:
            scraper = StorageAuctionsScraper(provider_id)
        else:
            return jsonify({
                'success': False,
                'error': 'No scraper available for this provider'
            }), 400

        # Run the scraper (with optional dry_run mode)
        # In production, you'd want to use Celery or similar for background tasks
        result = scraper.run_scraper(full_scrape=full_scrape, dry_run=dry_run)

        return jsonify({
            'success': True,
            'scrape_result': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/providers/<provider_id>/auctions', methods=['DELETE'])
@login_required
def purge_provider_auctions(provider_id):
    """Purge all auctions for a provider (admin only)"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get count before deletion
        cursor.execute("""
            SELECT COUNT(*) as count FROM auctions
            WHERE provider_id = %s
        """, (provider_id,))
        result = cursor.fetchone()
        auction_count = result['count'] if result else 0

        # Delete all auctions for this provider
        cursor.execute("""
            DELETE FROM auctions
            WHERE provider_id = %s
        """, (provider_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Deleted {auction_count} auctions for provider',
            'deleted_count': auction_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# User Management Endpoints
# ============================================================================

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all users (admin only)"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                user_id,
                username,
                email,
                first_name,
                last_name,
                role,
                is_active,
                email_verified,
                last_login_at,
                login_count,
                created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'users': users
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    try:
        data = request.get_json()

        # Validate required fields
        required = ['username', 'email', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Check if username or email already exists
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id FROM users
            WHERE username = %s OR email = %s
        """, (data['username'], data['email']))

        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Username or email already exists'
            }), 400

        # Hash password
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user
        cursor.execute("""
            INSERT INTO users (
                username,
                email,
                password_hash,
                first_name,
                last_name,
                role,
                is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id, username, email, role
        """, (
            data['username'],
            data['email'],
            password_hash,
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('role', 'regular'),
            data.get('is_active', True)
        ))

        user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'user': user
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user (admin only)"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        values = []

        if 'email' in data:
            update_fields.append('email = %s')
            values.append(data['email'])
        if 'first_name' in data:
            update_fields.append('first_name = %s')
            values.append(data['first_name'])
        if 'last_name' in data:
            update_fields.append('last_name = %s')
            values.append(data['last_name'])
        if 'role' in data:
            update_fields.append('role = %s')
            values.append(data['role'])
        if 'is_active' in data:
            update_fields.append('is_active = %s')
            values.append(data['is_active'])
        if 'password' in data and data['password']:
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            update_fields.append('password_hash = %s')
            values.append(password_hash)

        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
        cursor.execute(query, values)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user (admin only)"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        # Prevent deleting self
        if current_user.id == user_id:
            return jsonify({
                'success': False,
                'error': 'Cannot delete your own account'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Facilities Endpoints
# ============================================================================

@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    """Get all facilities, optionally filtered by provider"""
    try:
        provider_id = request.args.get('provider_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        if provider_id:
            cursor.execute("""
                SELECT
                    f.*,
                    p.name as provider_name,
                    COUNT(a.auction_id) as auction_count
                FROM facilities f
                LEFT JOIN providers p ON f.provider_id = p.provider_id
                LEFT JOIN auctions a ON f.facility_id = a.facility_id AND a.status = 'active'
                WHERE f.provider_id = %s
                GROUP BY f.facility_id, p.name
                ORDER BY f.facility_name
            """, (provider_id,))
        else:
            cursor.execute("""
                SELECT
                    f.*,
                    p.name as provider_name,
                    COUNT(a.auction_id) as auction_count
                FROM facilities f
                LEFT JOIN providers p ON f.provider_id = p.provider_id
                LEFT JOIN auctions a ON f.facility_id = a.facility_id AND a.status = 'active'
                GROUP BY f.facility_id, p.name
                ORDER BY p.name, f.facility_name
            """)

        facilities = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'facilities': facilities
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/facilities/<facility_id>', methods=['GET'])
def get_facility(facility_id):
    """Get a specific facility by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                f.*,
                p.name as provider_name,
                COUNT(a.auction_id) as auction_count
            FROM facilities f
            LEFT JOIN providers p ON f.provider_id = p.provider_id
            LEFT JOIN auctions a ON f.facility_id = a.facility_id AND a.status = 'active'
            WHERE f.facility_id = %s
            GROUP BY f.facility_id, p.name
        """, (facility_id,))

        facility = cursor.fetchone()
        cursor.close()
        conn.close()

        if not facility:
            return jsonify({
                'success': False,
                'error': 'Facility not found'
            }), 404

        return jsonify({
            'success': True,
            'facility': facility
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/facilities/<facility_id>', methods=['PUT'])
def update_facility(facility_id):
    """Update a facility"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if facility exists
        cursor.execute("SELECT facility_id FROM facilities WHERE facility_id = %s", (facility_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Facility not found'
            }), 404

        # Update facility
        cursor.execute("""
            UPDATE facilities SET
                facility_name = %s,
                address_line1 = %s,
                address_line2 = %s,
                city = %s,
                state = %s,
                zip_code = %s,
                phone = %s,
                email = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE facility_id = %s
        """, (
            data.get('facility_name'),
            data.get('address_line1'),
            data.get('address_line2'),
            data.get('city'),
            data.get('state'),
            data.get('zip_code'),
            data.get('phone'),
            data.get('email'),
            facility_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Facility updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/facilities/<facility_id>', methods=['DELETE'])
@login_required
def delete_facility(facility_id):
    """Delete a facility (admin only)"""
    if not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if facility has active auctions
        cursor.execute("""
            SELECT COUNT(*) as count FROM auctions
            WHERE facility_id = %s AND status = 'active'
        """, (facility_id,))

        result = cursor.fetchone()
        if result and result['count'] > 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete facility with {result["count"]} active auctions'
            }), 400

        # Delete facility
        cursor.execute("DELETE FROM facilities WHERE facility_id = %s", (facility_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Facility deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# Catch-All Route for Static Files (MUST BE LAST)
# ============================================================================

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (JSX, etc.)"""
    # Don't serve files starting with api/ or admin/
    if path.startswith('api/') or path.startswith('admin/'):
        return jsonify({'error': 'Not found'}), 404

    # Try to serve the file from the current directory
    file_path = os.path.join(app.root_path, path)
    if os.path.isfile(file_path):
        # Determine MIME type
        if path.endswith('.jsx'):
            mimetype = 'application/javascript'
        elif path.endswith('.js'):
            mimetype = 'application/javascript'
        elif path.endswith('.css'):
            mimetype = 'text/css'
        elif path.endswith('.json'):
            mimetype = 'application/json'
        else:
            mimetype = None

        return send_from_directory(app.root_path, path, mimetype=mimetype)

    # File not found - return 404 or index.html
    # For unknown paths that don't look like files, serve index.html (SPA routing)
    if '.' not in path:  # No extension = probably a route
        return render_template('index.html', api_base_url=API_BASE_URL)

    # Has extension but file not found = 404
    return jsonify({'error': 'File not found'}), 404


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# Run Server
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║       Storage Auction Platform API                        ║
    ║       Running on http://localhost:5000                    ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Available Endpoints:
    - GET  /api/auctions              - List all auctions
    - GET  /api/auctions/:id          - Get auction details
    - POST /api/auctions/:id/bids     - Place a bid
    - GET  /api/tags                  - Get all tags
    - GET  /api/search                - Advanced search
    - GET  /api/providers             - List providers
    - GET  /api/health                - Health check
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
