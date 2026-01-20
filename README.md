# Storage Auction Platform

A full-stack web application for discovering and bidding on storage unit auctions across California (expandable nationwide).

## 🎯 Features

### Frontend
- **Interactive Map** - OpenStreetMap integration via Leaflet.js showing auction locations
- **Tag-based Filtering** - Filter auctions by content type (furniture, electronics, tools, etc.)
- **Full-text Search** - Search across descriptions, locations, and tags
- **Detailed Auction Pages** - Complete auction information with image galleries, bid history, and maps
- **Real-time Bidding** - Place bids with automatic validation
- **Responsive Design** - Works on desktop, tablet, and mobile

### Backend
- **RESTful API** - Flask-based API with comprehensive endpoints
- **PostgreSQL Database** - Robust relational database with proper indexing
- **Web Scraping** - Automated scrapers for multiple auction providers
- **AI Image Analysis** - Automatic content detection and tagging
- **Address Geocoding** - Convert addresses to coordinates with multiple fallbacks

## 📁 Project Structure

```
storage-auction-platform/
├── frontend/
│   └── storage-auctions-enhanced.jsx   # React frontend
├── backend/
│   ├── api_backend.py                  # Flask REST API
│   ├── database_schema.sql             # PostgreSQL schema
│   ├── web_scraper.py                  # Auction scrapers
│   └── image_analysis_geocoding.py     # AI & geocoding services
├── .env.example                        # Environment variables template
└── README.md                           # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- (Optional) Hugging Face API token for image analysis

### 1. Database Setup

```bash
# Create database
createdb storage_auctions

# Run schema
psql -d storage_auctions -f database_schema.sql
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install flask flask-cors psycopg2-binary python-dotenv requests beautifulsoup4 pillow --break-system-packages

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# DATABASE_URL=postgresql://user:password@localhost:5432/storage_auctions
# SECRET_KEY=your-secret-key-here
# HUGGINGFACE_API_TOKEN=your-token (optional, for AI features)

# Run the API server
python api_backend.py
```

Server will start at `http://localhost:5000`

### 3. Frontend Setup

```bash
# The React component can be integrated into your existing React app
# or used as a standalone artifact

# If using as standalone, you'll need:
# - React
# - Tailwind CSS
# - Lucide React icons
# - Leaflet.js

# Install dependencies:
npm install react react-dom lucide-react

# For Leaflet:
# The component loads it dynamically from CDN, no install needed
```

### 4. Running Web Scrapers

```bash
# Run the scraper to populate database
python web_scraper.py

# Note: Customize scrapers for actual websites
# Check robots.txt and terms of service before scraping
```

### 5. AI Image Analysis & Geocoding

```bash
# Process auction images
python image_analysis_geocoding.py

# This will:
# - Analyze images with AI
# - Extract tags
# - Geocode addresses
# - Update database
```

## 🗄️ Database Schema

### Main Tables

- **users** - User accounts and authentication
- **providers** - Storage companies (StorageMart, Public Storage, etc.)
- **auctions** - Storage unit listings
- **bids** - Bid history
- **tags** - Content tags (furniture, electronics, tools, etc.)
- **auction_tags** - Junction table for many-to-many relationships
- **watchlist** - Users can watch auctions
- **notifications** - User notifications
- **scrape_logs** - Track scraping activity

### Key Features

- UUID primary keys for security
- Proper indexing for performance
- Triggers for automatic timestamp updates
- Views for common queries
- Support for multi-state expansion

## 🔌 API Endpoints

### Auctions
```
GET    /api/auctions              - List auctions (with filters)
GET    /api/auctions/:id          - Get auction details
POST   /api/auctions/:id/bids     - Place a bid
```

### Filtering Parameters
```
?state=CA                          - Filter by state
?city=Sacramento                   - Filter by city
?tags=furniture,tools              - Filter by tags
?search=electronics                - Search term
?sort=closing-soon                 - Sort order
?limit=50&offset=0                 - Pagination
```

### Other Endpoints
```
GET    /api/tags                   - Get all tags
GET    /api/search                 - Advanced search
GET    /api/providers              - List providers
GET    /api/health                 - Health check
```

## 🤖 AI Image Analysis

The platform supports multiple AI services for image analysis:

### Hugging Face (Free)
```python
export HUGGINGFACE_API_TOKEN="your_token"
```
- Model: BLIP or CLIP
- Free tier available
- Good for basic captioning

### Google Cloud Vision (Free Tier)
```python
export GOOGLE_VISION_API_KEY="your_key"
```
- 1000 requests/month free
- Excellent object detection
- High accuracy

### Azure Computer Vision (Free Tier)
```python
export AZURE_VISION_ENDPOINT="your_endpoint"
export AZURE_VISION_KEY="your_key"
```
- 5000 requests/month free
- Good performance
- Easy integration

## 📍 Geocoding

Address geocoding uses OpenStreetMap's Nominatim API (free, no API key required):

1. **Full Address** - Tries complete street address first
2. **City Level** - Falls back to city coordinates if address fails
3. **State Center** - Uses state center as last resort

**Rate Limiting:** Nominatim allows 1 request/second. The geocoder automatically respects this limit.

## 🏷️ Tag System

Tags are automatically generated from:
- AI image analysis (detected objects)
- Manual admin input
- User suggestions

Common tags:
- `furniture` - Chairs, tables, dressers
- `electronics` - TVs, computers, monitors
- `tools` - Power tools, hand tools
- `appliances` - Refrigerators, washers
- `sports` - Equipment, bikes, golf clubs
- `office` - Desks, filing cabinets
- `boxes` - Storage containers
- `premium` - High-value items

## 🔧 Web Scraping

### Important Notes

⚠️ **Always check:**
- `robots.txt` of target websites
- Terms of Service
- Rate limiting requirements

### Scraper Template

The provided scrapers are **templates** and need customization for real websites:

```python
class YourProviderScraper(StorageAuctionScraper):
    def scrape_auctions(self, state='CA'):
        # Customize selectors for your target site
        # Adjust parsing logic
        # Handle pagination
        pass
```

### Best Practices

1. **Respect robots.txt** - Check allowed paths
2. **Rate limiting** - Add delays between requests
3. **Use official APIs** - When available, use provider APIs instead
4. **Error handling** - Implement retry logic
5. **Logging** - Track all scraping activity
6. **User agent** - Identify your bot properly

## 📱 Frontend Integration

### Using with Existing React App

```jsx
import StorageAuctionApp from './storage-auctions-enhanced';

function App() {
  return (
    <div>
      <StorageAuctionApp />
    </div>
  );
}
```

### API Integration

Update the frontend to connect to your API:

```javascript
// Replace mock data with API calls
const fetchAuctions = async () => {
  const response = await fetch('http://localhost:5000/api/auctions?state=CA');
  const data = await response.json();
  setAuctions(data.auctions);
};
```

## 🌍 Expanding Beyond California

The database is designed for nationwide expansion:

1. **Update state filter** - Change default from 'CA' to 'all'
2. **Add state scrapers** - Create scrapers for other states
3. **Adjust UI** - Update location selector in frontend
4. **Optimize queries** - Ensure indexes work for larger dataset

## 🔐 Security Considerations

### For Production

- [ ] Implement proper authentication (JWT tokens)
- [ ] Add rate limiting on API endpoints
- [ ] Use HTTPS only
- [ ] Sanitize all user inputs
- [ ] Implement CSRF protection
- [ ] Use environment variables for all secrets
- [ ] Add API key authentication
- [ ] Implement proper CORS policies
- [ ] Add SQL injection protection (use parameterized queries)
- [ ] Set up logging and monitoring

## 📊 Performance Optimization

### Database
- Proper indexing on frequently queried columns
- Use connection pooling
- Cache frequent queries
- Optimize complex joins

### API
- Implement pagination
- Add response caching
- Use CDN for static assets
- Compress responses (gzip)

### Frontend
- Lazy load images
- Virtual scrolling for large lists
- Debounce search inputs
- Cache map tiles

## 🧪 Testing

```bash
# Test API health
curl http://localhost:5000/api/health

# Test auction listing
curl http://localhost:5000/api/auctions?state=CA&limit=5

# Test specific auction
curl http://localhost:5000/api/auctions/[auction-id]

# Test geocoding
python -c "from image_analysis_geocoding import GeocodeService; g = GeocodeService(); print(g.geocode_address('123 Main St', 'Sacramento', 'CA', '95814'))"
```

## 📝 TODO / Future Features

- [ ] User authentication and profiles
- [ ] Email notifications for outbid alerts
- [ ] Mobile app (React Native)
- [ ] Payment processing integration
- [ ] Auction winner verification system
- [ ] Advanced analytics dashboard
- [ ] SMS notifications
- [ ] Auto-bidding (proxy bidding)
- [ ] Social features (share auctions)
- [ ] Auction recommendations (ML-based)

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -l | grep storage_auctions
```

### Geocoding Rate Limits
```
Error: Too many requests
Solution: Increase delay between requests in geocoder
```

### Map Not Loading
```
Issue: Leaflet not loading
Solution: Check browser console, ensure internet connection for CDN
```

### AI Analysis Failing
```
Issue: No API token
Solution: Set HUGGINGFACE_API_TOKEN in .env file
```

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ for storage auction enthusiasts
