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

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import List, Dict, Optional
import json

# Import our helper modules
# from image_analysis_geocoding import GeocodeService, ImageAnalysisService


app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/storage_auctions')


# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection():
    """Create database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


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
# API Routes - Providers
# ============================================================================

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get all storage providers"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, COUNT(a.auction_id) as active_auctions
            FROM providers p
            LEFT JOIN auctions a ON p.provider_id = a.provider_id AND a.status = 'active'
            WHERE p.is_active = TRUE
            GROUP BY p.provider_id
            ORDER BY p.name
        """)
        
        providers = [dict(row) for row in cursor.fetchall()]
        
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
