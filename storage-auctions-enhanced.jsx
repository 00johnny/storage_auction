// Browser-compatible version - no imports needed, using global React
const { useState, useEffect, useRef } = React;

// Simple icon components using SVG
const MapPin = () => <span>📍</span>;
const Clock = () => <span>⏰</span>;
const DollarSign = () => <span>💰</span>;
const Package = () => <span>📦</span>;
const Search = () => <span>🔍</span>;
const Filter = () => <span>🔽</span>;
const X = () => <span>✖</span>;
const Tag = () => <span>🏷️</span>;
const Eye = () => <span>👁️</span>;
const ChevronLeft = () => <span>◀</span>;
const ChevronRight = () => <span>▶</span>;
const ImageIcon = () => <span>🖼️</span>;

const StorageAuctionApp = () => {
  const [auctions, setAuctions] = useState([]);
  const [filteredAuctions, setFilteredAuctions] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('all');
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [selectedTags, setSelectedTags] = useState([]);
  const [sortBy, setSortBy] = useState('closing-soon');
  const [zipcode, setZipcode] = useState('');
  const [maxDistance, setMaxDistance] = useState('');
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'detail'
  const [selectedAuction, setSelectedAuction] = useState(null);
  const [allTags, setAllTags] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  // Load saved filters from localStorage when user logs in
  useEffect(() => {
    if (currentUser) {
      const savedFilters = localStorage.getItem(`filters_${currentUser.user_id}`);
      if (savedFilters) {
        try {
          const filters = JSON.parse(savedFilters);
          setSearchTerm(filters.searchTerm || '');
          setSelectedCity(filters.selectedCity || 'all');
          setSelectedProvider(filters.selectedProvider || 'all');
          setSelectedTags(filters.selectedTags || []);
          setSortBy(filters.sortBy || 'closing-soon');
          setZipcode(filters.zipcode || '');
          setMaxDistance(filters.maxDistance || '');
        } catch (e) {
          console.error('Error loading saved filters:', e);
        }
      }
    }
  }, [currentUser]);

  // Save filters to localStorage when they change (if user logged in)
  useEffect(() => {
    if (currentUser) {
      const filters = {
        searchTerm,
        selectedCity,
        selectedProvider,
        selectedTags,
        sortBy,
        zipcode,
        maxDistance
      };
      localStorage.setItem(`filters_${currentUser.user_id}`, JSON.stringify(filters));
    }
  }, [currentUser, searchTerm, selectedCity, selectedProvider, selectedTags, sortBy, zipcode, maxDistance]);

  // Fetch data from backend API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        // Get API base URL from injected config and normalize (remove trailing slash)
        const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');

        // Build query parameters for distance filtering
        let queryParams = new URLSearchParams();
        if (zipcode) {
          queryParams.append('zipcode', zipcode);
          if (maxDistance) {
            queryParams.append('distance', maxDistance);
          }
        }
        if (sortBy === 'distance' && zipcode) {
          queryParams.append('sort', 'distance');
        }

        const queryString = queryParams.toString();
        const auctionsUrl = queryString ? `${apiBaseUrl}/api/auctions?${queryString}` : `${apiBaseUrl}/api/auctions`;

        // Fetch auctions
        const auctionsResponse = await fetch(auctionsUrl);
        const auctionsData = await auctionsResponse.json();

        if (auctionsData.success) {
          // Map backend data to frontend format
          const mappedAuctions = auctionsData.auctions.map(auction => ({
            id: auction.auction_id,
            unitNumber: auction.unit_number,
            facilityName: auction.facility_name || 'Unknown Facility',
            provider: auction.provider_name,
            city: auction.city,
            state: auction.state,
            zipCode: auction.zip_code,
            address: `${auction.address_line1 || ''}, ${auction.city}, ${auction.state} ${auction.zip_code}`,
            latitude: auction.latitude,
            longitude: auction.longitude,
            closingDate: auction.closes_at,
            currentBid: parseFloat(auction.current_bid) || 0,
            minimumBid: parseFloat(auction.minimum_bid) || 0,
            bidIncrement: parseFloat(auction.bid_increment) || 25,
            unitSize: auction.unit_size,
            description: auction.description || 'No description available',
            aiDescription: auction.ai_description || '',
            imageUrls: auction.image_urls || [],
            totalBids: auction.total_bids || 0,
            tags: auction.tags || [],
            bidHistory: [],
            sourceUrl: auction.source_url,
            fullnessRating: auction.fullness_rating,
            distanceMiles: auction.distance_miles
          }));

          setAuctions(mappedAuctions);
          setFilteredAuctions(mappedAuctions);

          // Extract all unique tags
          const tags = [...new Set(mappedAuctions.flatMap(a => a.tags))];
          setAllTags(tags);
        }

        // Fetch tags
        const tagsResponse = await fetch(`${apiBaseUrl}/api/tags`);
        const tagsData = await tagsResponse.json();

        if (tagsData.success && tagsData.tags.length > 0) {
          const tagNames = tagsData.tags.map(t => t.tag_name);
          setAllTags(tagNames);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        // Fall back to empty state
        setAuctions([]);
        setFilteredAuctions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [zipcode, maxDistance, sortBy]);

  // Check if user is authenticated (for admin features)
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');
        const response = await fetch(`${apiBaseUrl}/api/auth/check`, {
          credentials: 'include'
        });
        const data = await response.json();
        if (data.authenticated) {
          setCurrentUser(data.user);
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
      }
    };

    checkAuth();
  }, []);

  // OLD MOCK DATA BELOW (keeping for reference, but not used)
  useEffect(() => {
    return; // This effect is disabled
    const mockAuctions = [
      {
        id: 1,
        unitNumber: 'A-127',
        provider: 'StorageMart Sacramento',
        city: 'Sacramento',
        state: 'CA',
        zipCode: '95814',
        address: '1234 Main St, Sacramento, CA 95814',
        latitude: 38.5816,
        longitude: -121.4944,
        closingDate: '2026-01-22T15:00:00',
        currentBid: 450,
        minimumBid: 300,
        bidIncrement: 25,
        unitSize: '10x10',
        description: 'Household items, boxes visible from door. Contains various furniture pieces including what appears to be a dresser and chairs. Multiple cardboard boxes stacked along the walls.',
        aiDescription: 'AI Analysis: Detected furniture (dresser, chairs), cardboard boxes, possible household appliances',
        imageUrls: ['https://via.placeholder.com/800x600?text=Unit+A-127'],
        totalBids: 12,
        tags: ['furniture', 'boxes', 'household'],
        bidHistory: [
          { amount: 300, user: 'user123', time: '2026-01-19T10:00:00' },
          { amount: 350, user: 'user456', time: '2026-01-19T11:30:00' },
          { amount: 450, user: 'user789', time: '2026-01-19T14:15:00' }
        ]
      },
      {
        id: 2,
        unitNumber: 'B-45',
        provider: 'Public Storage Los Angeles',
        city: 'Los Angeles',
        state: 'CA',
        zipCode: '90012',
        address: '456 Storage Ave, Los Angeles, CA 90012',
        latitude: 34.0522,
        longitude: -118.2437,
        closingDate: '2026-01-20T12:00:00',
        currentBid: 875,
        minimumBid: 500,
        bidIncrement: 50,
        unitSize: '10x20',
        description: 'Furniture, appliances, appears well-maintained. Large refrigerator visible, leather couch, dining table set. Clean and organized storage.',
        aiDescription: 'AI Analysis: Detected appliances (refrigerator), furniture (couch, dining table), good condition items',
        imageUrls: ['https://via.placeholder.com/800x600?text=Unit+B-45'],
        totalBids: 28,
        tags: ['furniture', 'appliances', 'premium'],
        bidHistory: [
          { amount: 500, user: 'user111', time: '2026-01-18T09:00:00' },
          { amount: 650, user: 'user222', time: '2026-01-18T15:00:00' },
          { amount: 875, user: 'user333', time: '2026-01-19T08:30:00' }
        ]
      },
      {
        id: 3,
        unitNumber: 'C-302',
        provider: 'Extra Space Storage San Diego',
        city: 'San Diego',
        state: 'CA',
        zipCode: '92101',
        address: '789 Ocean Blvd, San Diego, CA 92101',
        latitude: 32.7157,
        longitude: -117.1611,
        closingDate: '2026-01-19T18:00:00',
        currentBid: 225,
        minimumBid: 150,
        bidIncrement: 25,
        unitSize: '5x10',
        description: 'Small unit, mixed contents. Various boxes, some tools visible, random household items.',
        aiDescription: 'AI Analysis: Detected tools, boxes, miscellaneous items',
        imageUrls: ['https://via.placeholder.com/800x600?text=Unit+C-302'],
        totalBids: 8,
        tags: ['tools', 'boxes', 'miscellaneous'],
        bidHistory: [
          { amount: 150, user: 'user444', time: '2026-01-18T12:00:00' },
          { amount: 225, user: 'user555', time: '2026-01-19T09:00:00' }
        ]
      },
      {
        id: 4,
        unitNumber: 'D-88',
        provider: 'CubeSmart San Francisco',
        city: 'San Francisco',
        state: 'CA',
        zipCode: '94102',
        address: '321 Tech Plaza, San Francisco, CA 94102',
        latitude: 37.7749,
        longitude: -122.4194,
        closingDate: '2026-01-21T14:00:00',
        currentBid: 1200,
        minimumBid: 800,
        bidIncrement: 50,
        unitSize: '10x15',
        description: 'Electronics, office equipment visible. Multiple monitors, desktop computers, office chairs, filing cabinets. Potential tech liquidation.',
        aiDescription: 'AI Analysis: Detected electronics (monitors, computers), office furniture, high-value potential',
        imageUrls: ['https://via.placeholder.com/800x600?text=Unit+D-88'],
        totalBids: 35,
        tags: ['electronics', 'office', 'computers', 'premium'],
        bidHistory: [
          { amount: 800, user: 'user666', time: '2026-01-18T10:00:00' },
          { amount: 1000, user: 'user777', time: '2026-01-19T11:00:00' },
          { amount: 1200, user: 'user888', time: '2026-01-19T13:45:00' }
        ]
      },
      {
        id: 5,
        unitNumber: 'E-156',
        provider: 'Life Storage Fresno',
        city: 'Fresno',
        state: 'CA',
        zipCode: '93721',
        address: '555 Valley Way, Fresno, CA 93721',
        latitude: 36.7378,
        longitude: -119.7871,
        closingDate: '2026-01-23T16:00:00',
        currentBid: 325,
        minimumBid: 200,
        bidIncrement: 25,
        unitSize: '10x10',
        description: 'Tools, sporting goods, general household. Power tools, golf clubs, bicycles, camping equipment visible.',
        aiDescription: 'AI Analysis: Detected sports equipment, tools, outdoor gear',
        imageUrls: ['https://via.placeholder.com/800x600?text=Unit+E-156'],
        totalBids: 15,
        tags: ['tools', 'sports', 'outdoor', 'household'],
        bidHistory: [
          { amount: 200, user: 'user999', time: '2026-01-19T08:00:00' },
          { amount: 275, user: 'user101', time: '2026-01-19T10:30:00' },
          { amount: 325, user: 'user102', time: '2026-01-19T12:00:00' }
        ]
      }
    ];
    
    setAuctions(mockAuctions);
    setFilteredAuctions(mockAuctions);
    
    // Extract all unique tags
    const tags = [...new Set(mockAuctions.flatMap(a => a.tags))];
    setAllTags(tags);
  }, []);

  // Initialize Leaflet map
  useEffect(() => {
    if (viewMode === 'list' && mapRef.current && !mapInstanceRef.current && typeof window !== 'undefined') {
      // Dynamically load Leaflet
      const loadLeaflet = async () => {
        if (!window.L) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
          document.head.appendChild(link);

          const script = document.createElement('script');
          script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
          script.async = true;
          
          await new Promise((resolve) => {
            script.onload = resolve;
            document.head.appendChild(script);
          });
        }

        if (window.L && mapRef.current) {
          const map = window.L.map(mapRef.current).setView([36.7783, -119.4179], 6); // Center of California
          
          window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
          }).addTo(map);

          mapInstanceRef.current = map;

          // Group auctions by facility (same location = same facility)
          const facilities = {};
          filteredAuctions.forEach(auction => {
            if (auction.latitude && auction.longitude) {
              const key = `${auction.latitude},${auction.longitude}`;
              if (!facilities[key]) {
                facilities[key] = {
                  lat: auction.latitude,
                  lon: auction.longitude,
                  facilityName: auction.facilityName,
                  city: auction.city,
                  state: auction.state,
                  provider: auction.provider,
                  auctions: []
                };
              }
              facilities[key].auctions.push(auction);
            }
          });

          // Add one marker per facility
          Object.values(facilities).forEach(facility => {
            const marker = window.L.marker([facility.lat, facility.lon]).addTo(map);

            // Build popup with facility info and auction list
            const auctionCount = facility.auctions.length;
            const auctionList = facility.auctions
              .slice(0, 5)  // Show max 5 auctions
              .map(a => `<li>Unit ${a.unitNumber} - $${a.currentBid} (${a.unitSize})</li>`)
              .join('');
            const moreText = auctionCount > 5 ? `<p><em>...and ${auctionCount - 5} more</em></p>` : '';

            marker.bindPopup(`
              <div style="min-width: 250px;">
                <strong>${facility.facilityName}</strong><br/>
                <small>${facility.provider}</small><br/>
                ${facility.city}, ${facility.state}<br/>
                <hr style="margin: 8px 0;"/>
                <strong>${auctionCount} Auction${auctionCount > 1 ? 's' : ''}</strong>
                <ul style="margin: 5px 0; padding-left: 20px; font-size: 0.9em;">
                  ${auctionList}
                </ul>
                ${moreText}
                <button
                  onclick="window.dispatchEvent(new CustomEvent('viewFacility', {detail: {facilityName: '${facility.facilityName}'}}))"
                  style="margin-top: 8px; padding: 4px 8px; background: #3B82F6; color: white; border: none; border-radius: 4px; cursor: pointer;"
                >
                  View All Auctions
                </button>
              </div>
            `);

            // Click marker to view first auction in detail
            marker.on('click', () => {
              if (facility.auctions.length > 0) {
                setSelectedAuction(facility.auctions[0]);
                setViewMode('detail');
              }
            });
          });
        }
      };

      loadLeaflet();
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [viewMode, filteredAuctions]);

  // Filter and sort auctions
  useEffect(() => {
    let filtered = [...auctions];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(auction =>
        auction.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        auction.provider.toLowerCase().includes(searchTerm.toLowerCase()) ||
        auction.zipCode.includes(searchTerm) ||
        auction.unitNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        auction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        auction.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // City filter
    if (selectedCity !== 'all') {
      filtered = filtered.filter(auction => auction.city === selectedCity);
    }

    // Provider filter
    if (selectedProvider !== 'all') {
      filtered = filtered.filter(auction => auction.provider === selectedProvider);
    }

    // Tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter(auction =>
        selectedTags.every(tag => auction.tags.includes(tag))
      );
    }

    // Sort
    if (sortBy === 'closing-soon') {
      filtered.sort((a, b) => new Date(a.closingDate) - new Date(b.closingDate));
    } else if (sortBy === 'highest-bid') {
      filtered.sort((a, b) => b.currentBid - a.currentBid);
    } else if (sortBy === 'lowest-bid') {
      filtered.sort((a, b) => a.currentBid - b.currentBid);
    }

    setFilteredAuctions(filtered);
  }, [searchTerm, selectedCity, selectedProvider, selectedTags, sortBy, auctions]);

  const getTimeRemaining = (closingDate) => {
    const now = new Date();
    const close = new Date(closingDate);
    const diff = close - now;

    if (diff < 0) return 'Closed';

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const toggleTag = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const cities = ['all', ...new Set(auctions.map(a => a.city))];
  const providers = ['all', ...new Set(auctions.map(a => a.provider).filter(p => p))];

  // Detail Page Component
  const AuctionDetailPage = ({ auction }) => {
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [bidAmount, setBidAmount] = useState('');

    const handlePlaceBid = () => {
      alert(`Bid of $${bidAmount} placed! (This is a demo)`);
      setBidAmount('');
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => setViewMode('list')}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              Back to Listings
            </button>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Images & Details */}
            <div className="lg:col-span-2 space-y-6">
              {/* Image Gallery */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="relative h-96 bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                  {auction.imageUrls && auction.imageUrls.length > 0 ? (
                    <img
                      src={auction.imageUrls[currentImageIndex]}
                      alt={`Unit ${auction.unitNumber}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <ImageIcon className="w-24 h-24 text-slate-400" />
                  )}
                  
                  {auction.imageUrls && auction.imageUrls.length > 1 && (
                    <>
                      <button
                        onClick={() => setCurrentImageIndex(Math.max(0, currentImageIndex - 1))}
                        className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white p-2 rounded-full shadow-lg"
                        disabled={currentImageIndex === 0}
                      >
                        <ChevronLeft className="w-6 h-6" />
                      </button>
                      <button
                        onClick={() => setCurrentImageIndex(Math.min(auction.imageUrls.length - 1, currentImageIndex + 1))}
                        className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white p-2 rounded-full shadow-lg"
                        disabled={currentImageIndex === auction.imageUrls.length - 1}
                      >
                        <ChevronRight className="w-6 h-6" />
                      </button>
                    </>
                  )}
                </div>
                
                {auction.imageUrls && auction.imageUrls.length > 1 && (
                  <div className="p-4 flex gap-2 overflow-x-auto">
                    {auction.imageUrls.map((url, idx) => (
                      <button
                        key={idx}
                        onClick={() => setCurrentImageIndex(idx)}
                        className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                          idx === currentImageIndex ? 'border-blue-500' : 'border-slate-200'
                        }`}
                      >
                        <img src={url} alt={`Thumbnail ${idx + 1}`} className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Description */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Description</h2>
                <p className="text-slate-700 mb-4">{auction.description}</p>
                
                {auction.aiDescription && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-900 font-medium">{auction.aiDescription}</p>
                  </div>
                )}
              </div>

              {/* Location & Map */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Location</h2>
                <div className="flex items-start gap-2 text-slate-700 mb-4">
                  <MapPin className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">{auction.provider}</p>
                    <p>{auction.address}</p>
                  </div>
                </div>
                
                <div id="detail-map" className="h-64 rounded-lg overflow-hidden bg-slate-100" ref={(el) => {
                  if (el && !el.querySelector('.leaflet-container')) {
                    setTimeout(() => {
                      if (window.L && auction.latitude && auction.longitude) {
                        const detailMap = window.L.map(el).setView([auction.latitude, auction.longitude], 13);
                        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                          attribution: '© OpenStreetMap contributors'
                        }).addTo(detailMap);
                        window.L.marker([auction.latitude, auction.longitude]).addTo(detailMap);
                      }
                    }, 100);
                  }
                }}></div>
              </div>

              {/* Bid History */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Bid History</h2>
                <div className="space-y-3">
                  {auction.bidHistory && auction.bidHistory.map((bid, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                          <span className="text-xs font-semibold text-slate-700">#{auction.bidHistory.length - idx}</span>
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">${bid.amount}</p>
                          <p className="text-xs text-slate-500">
                            {new Date(bid.time).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <span className="text-sm text-slate-500">{bid.user}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column - Bidding */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sticky top-8">
                <div className="mb-6">
                  <h1 className="text-2xl font-bold text-slate-900 mb-2">
                    {auction.facilityName} - {auction.unitNumber}
                  </h1>
                  <div className="flex items-center gap-2 flex-wrap mb-4">
                    {auction.tags.map(tag => (
                      <span key={tag} className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <span className="bg-slate-100 text-slate-700 text-sm font-medium px-3 py-1.5 rounded-lg">
                    {auction.unitSize}
                  </span>
                  {auction.fullnessRating && (
                    <div className="mt-3 bg-blue-50 rounded-lg p-2">
                      <p className="text-xs text-slate-600 mb-1">🤖 AI Fullness Estimate</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{width: `${auction.fullnessRating}%`}}
                          ></div>
                        </div>
                        <span className="text-sm font-semibold text-slate-700">{auction.fullnessRating}%</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Current Bid */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-700 mb-1">Current Bid</p>
                  <p className="text-3xl font-bold text-blue-900">${auction.currentBid}</p>
                  <p className="text-xs text-blue-600 mt-1">{auction.totalBids} bids placed</p>
                </div>

                {/* Time Remaining */}
                <div className="bg-slate-50 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-2 text-slate-600 text-sm mb-1">
                    <Clock className="w-4 h-4" />
                    <span>Closing In</span>
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{getTimeRemaining(auction.closingDate)}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(auction.closingDate).toLocaleString()}
                  </p>
                </div>

                {/* Bidding Info */}
                <div className="border-t border-slate-200 pt-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <p className="text-sm text-blue-800">
                      To place a bid on this auction, visit the auction source website.
                    </p>
                  </div>

                  {auction.sourceUrl && (
                    <a
                      href={auction.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <span>🔗</span>
                      View on Source Site
                    </a>
                  )}

                  <button className="w-full mt-3 border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold py-3 rounded-lg transition-colors">
                    Add to Watchlist
                  </button>

                  {/* Admin Tools (only visible to admins) */}
                  {currentUser && currentUser.role === 'admin' && (
                    <div className="mt-8 pt-6 border-t border-slate-200">
                      <h3 className="font-semibold text-sm text-slate-700 mb-3">Admin Tools</h3>
                      <button
                        onClick={async () => {
                          if (!confirm('Re-fetch this auction detail from source?\n\nThis will update:\n• Full description\n• Tags/categories\n• Images\n• Current bid\n• Other detail-page data')) return;

                          try {
                            const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');
                            const response = await fetch(`${apiBaseUrl}/api/auctions/${auction.id}/refetch`, {
                              method: 'POST',
                              credentials: 'include'
                            });
                            const result = await response.json();

                            if (result.success) {
                              const data = result.data;
                              alert(`✓ ${result.message}\n\n` +
                                    `Description: ${data.description_updated ? 'Updated' : 'No change'}\n` +
                                    `Images: ${data.images_found} found\n` +
                                    `Tags: ${data.tags_found} found\n` +
                                    `Fields updated: ${data.fields_updated}\n` +
                                    `Current bid: $${data.current_bid || 'N/A'}`);
                              window.location.reload();
                            } else {
                              alert('Error: ' + result.error);
                            }
                          } catch (error) {
                            alert('Error re-fetching auction: ' + error.message);
                          }
                        }}
                        className="w-full bg-slate-600 hover:bg-slate-700 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                      >
                        <span>🔄</span>
                        Re-fetch Detail from Source
                      </button>

                      <button
                        onClick={async () => {
                          if (!confirm('Analyze auction images with AI?\n\nThis will:\n• Generate detailed item description\n• Estimate fullness (0-100%)\n• Identify item categories\n• Detect valuable items')) return;

                          try {
                            const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');
                            const response = await fetch(`${apiBaseUrl}/api/auctions/${auction.id}/analyze-images`, {
                              method: 'POST',
                              credentials: 'include',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ provider: 'huggingface' })
                            });
                            const result = await response.json();

                            if (result.success) {
                              const analysis = result.analysis;
                              alert(`✓ Images Analyzed!\n\n` +
                                    `Description: ${analysis.description}\n\n` +
                                    `Fullness: ${analysis.fullness_rating}%\n` +
                                    `Condition: ${analysis.condition}\n` +
                                    `Items: ${analysis.items.join(', ') || 'None detected'}\n` +
                                    `Categories: ${analysis.categories.join(', ') || 'None'}\n` +
                                    `Valuable items: ${analysis.valuable_items ? 'Yes' : 'No'}`);
                              window.location.reload();
                            } else {
                              alert('Error: ' + result.error);
                            }
                          } catch (error) {
                            alert('Error analyzing images: ' + error.message);
                          }
                        }}
                        className="w-full mt-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                      >
                        <span>🤖</span>
                        Analyze Images with AI
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  };

  // My Account Page Component
  const MyAccountPage = () => {
    const [formData, setFormData] = useState({
      username: currentUser?.username || '',
      email: currentUser?.email || '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    const [message, setMessage] = useState('');

    const handleSave = async () => {
      try {
        const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');

        // Update email
        const updateData = { email: formData.email };

        // Include password if changing
        if (formData.newPassword) {
          if (formData.newPassword !== formData.confirmPassword) {
            alert('New passwords do not match!');
            return;
          }
          if (formData.newPassword.length < 6) {
            alert('Password must be at least 6 characters!');
            return;
          }
          updateData.password = formData.newPassword;
        }

        const response = await fetch(`${apiBaseUrl}/api/users/${currentUser.user_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(updateData)
        });

        const result = await response.json();

        if (result.success) {
          setMessage('Profile updated successfully!');
          setFormData({...formData, currentPassword: '', newPassword: '', confirmPassword: ''});
          setTimeout(() => window.location.reload(), 1500);
        } else {
          alert('Error: ' + result.error);
        }
      } catch (error) {
        alert('Error updating profile: ' + error.message);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <header className="bg-white shadow-sm border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => setViewMode('list')}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              Back to Listings
            </button>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
            <h1 className="text-2xl font-bold text-slate-900 mb-6">My Account</h1>

            {message && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-green-800">{message}</p>
              </div>
            )}

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Username</label>
                <input
                  type="text"
                  value={formData.username}
                  disabled
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 bg-slate-100 text-slate-600"
                />
                <p className="text-xs text-slate-500 mt-1">Username cannot be changed</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="border-t border-slate-200 pt-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Change Password</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">New Password</label>
                    <input
                      type="password"
                      value={formData.newPassword}
                      onChange={(e) => setFormData({...formData, newPassword: e.target.value})}
                      placeholder="Leave blank to keep current password"
                      className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Confirm New Password</label>
                    <input
                      type="password"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                      placeholder="Confirm new password"
                      className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={handleSave}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className="px-6 border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold py-3 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  };

  // Main List View
  if (viewMode === 'detail' && selectedAuction) {
    return <AuctionDetailPage auction={selectedAuction} />;
  }

  if (viewMode === 'account') {
    return <MyAccountPage />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Storage Auctions</h1>
              <p className="text-slate-600 mt-1">Find storage unit auctions in California</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-blue-50 px-4 py-2 rounded-lg">
                <MapPin className="w-5 h-5 text-blue-600" />
                <span className="font-semibold text-blue-900">California</span>
              </div>
              {currentUser ? (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setViewMode('account')}
                    className="text-slate-700 hover:text-blue-600 font-medium"
                  >
                    👤 {currentUser.username}
                  </button>
                  <button
                    onClick={async () => {
                      const apiBaseUrl = (window.APP_CONFIG?.API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '');
                      await fetch(`${apiBaseUrl}/api/auth/logout`, {
                        method: 'POST',
                        credentials: 'include'
                      });
                      window.location.href = '/';
                    }}
                    className="text-slate-600 hover:text-slate-900 text-sm"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <a
                  href="/login"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Login
                </a>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Map Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
          <div className="p-4 border-b border-slate-200 bg-slate-50">
            <h2 className="text-lg font-semibold text-slate-900">Auction Locations</h2>
            <p className="text-sm text-slate-600">Click markers to view auction details</p>
          </div>
          <div ref={mapRef} className="h-96 w-full"></div>
        </div>

        {/* Filters Bar */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by keyword, city, or tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* City Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <select
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
              >
                {cities.map(city => (
                  <option key={city} value={city}>
                    {city === 'all' ? 'All Cities' : city}
                  </option>
                ))}
              </select>
            </div>

            {/* Provider Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
              >
                {providers.map(provider => (
                  <option key={provider} value={provider}>
                    {provider === 'all' ? 'All Providers' : provider}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
            >
              <option value="closing-soon">Closing Soon</option>
              <option value="highest-bid">Highest Bid</option>
              <option value="lowest-bid">Lowest Bid</option>
              {zipcode && <option value="distance">Nearest First</option>}
            </select>
          </div>

          {/* Distance Search Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-200">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                📍 Search by ZIP Code
              </label>
              <input
                type="text"
                placeholder="Enter ZIP code (e.g., 95672)"
                value={zipcode}
                onChange={(e) => setZipcode(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                maxLength="5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                📏 Max Distance (miles)
              </label>
              <input
                type="number"
                placeholder="e.g., 50"
                value={maxDistance}
                onChange={(e) => setMaxDistance(e.target.value)}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="1"
                disabled={!zipcode}
              />
            </div>
            <div className="flex items-end">
              {zipcode && (
                <button
                  onClick={() => {
                    setZipcode('');
                    setMaxDistance('');
                  }}
                  className="w-full px-4 py-2.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
                >
                  Clear Location Search
                </button>
              )}
            </div>
          </div>

          {/* Tag Cloud */}
          <div className="border-t border-slate-200 pt-4">
            <div className="flex items-center gap-2 mb-3">
              <Tag className="w-4 h-4 text-slate-600" />
              <span className="text-sm font-medium text-slate-700">Filter by Tags:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedTags.includes(tag)
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {tag}
                  {selectedTags.includes(tag) && (
                    <X className="inline-block w-3 h-3 ml-1" />
                  )}
                </button>
              ))}
            </div>
            {selectedTags.length > 0 && (
              <button
                onClick={() => setSelectedTags([])}
                className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Clear all tags
              </button>
            )}
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-slate-600 border-t border-slate-200 pt-4">
            <span>
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></span>
                  Loading auctions...
                </span>
              ) : (
                `${filteredAuctions.length} auctions found`
              )}
            </span>
            {selectedTags.length > 0 && (
              <span className="text-blue-600">
                Filtered by: {selectedTags.join(', ')}
              </span>
            )}
          </div>
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center justify-center py-12 bg-white rounded-xl shadow-sm border border-slate-200 mb-8">
            <div className="text-center">
              <div className="animate-spin inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mb-4"></div>
              <p className="text-slate-600 font-medium">
                {zipcode ? 'Calculating distances...' : 'Loading auctions...'}
              </p>
              {zipcode && <p className="text-sm text-slate-500 mt-2">This may take a moment for distance-based searches</p>}
            </div>
          </div>
        )}

        {/* Auction Grid */}
        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAuctions.map(auction => (
            <div
              key={auction.id}
              className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Auction Image Placeholder */}
              <div className="h-48 bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                <Package className="w-16 h-16 text-slate-400" />
              </div>

              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3
                      onClick={() => {
                        setSelectedAuction(auction);
                        setViewMode('detail');
                      }}
                      className="font-bold text-lg text-slate-900 cursor-pointer hover:text-blue-600 transition-colors"
                    >
                      {auction.facilityName} - {auction.unitNumber}
                    </h3>
                    <p className="text-sm text-slate-600">{auction.provider}</p>
                  </div>
                  <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded">
                    {auction.unitSize}
                  </span>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {auction.tags.map(tag => (
                    <span key={tag} className="bg-slate-100 text-slate-700 text-xs px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Location */}
                <div className="flex items-center gap-2 text-sm text-slate-600 mb-3">
                  <MapPin className="w-4 h-4" />
                  <span>{auction.city}, {auction.state} {auction.zipCode}</span>
                  {auction.distanceMiles && (
                    <span className="ml-auto text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-semibold">
                      {auction.distanceMiles} mi
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-sm text-slate-700 mb-4 line-clamp-2">
                  {auction.description}
                </p>

                {/* Bid Info */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-slate-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-slate-600 text-xs mb-1">
                      <DollarSign className="w-3.5 h-3.5" />
                      <span>Current Bid</span>
                    </div>
                    <p className="font-bold text-lg text-slate-900">${auction.currentBid}</p>
                    <p className="text-xs text-slate-500">{auction.totalBids} bids</p>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-slate-600 text-xs mb-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Closing In</span>
                    </div>
                    <p className="font-bold text-lg text-slate-900">{getTimeRemaining(auction.closingDate)}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(auction.closingDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                </div>

                {/* Action Button */}
                <button
                  onClick={() => {
                    setSelectedAuction(auction);
                    setViewMode('detail');
                  }}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors"
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredAuctions.length === 0 && (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-slate-200">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">No auctions found</h3>
            <p className="text-slate-500">Try adjusting your search or filters</p>
          </div>
        )}
      </main>
    </div>
  );
};

// No export needed - component is globally available in browser