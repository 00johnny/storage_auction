# AI Image Analysis for Storage Auctions

This system analyzes storage unit auction photos using AI to automatically:
- Generate detailed descriptions of visible items
- Estimate how full the unit is (0-100%)
- Categorize items (furniture, appliances, boxes, etc.)
- Detect potentially valuable items

## Features

### Supported AI Providers

The system is built with an extensible architecture allowing easy swapping between providers:

1. **Hugging Face** (Default - Free Tier)
   - Model: BLIP Image Captioning
   - Cost: Free with rate limits
   - Setup: Sign up at https://huggingface.co/settings/tokens
   - Best for: Testing and low-volume usage

2. **OpenAI GPT-4 Vision** (Coming Soon)
   - Cost: ~$0.01-0.03 per image
   - Setup: OpenAI API key required
   - Best for: Production with high accuracy needs

3. **Anthropic Claude Vision** (Coming Soon)
   - Cost: ~$0.01-0.03 per image
   - Setup: Anthropic API key required
   - Best for: Production with excellent accuracy

## Setup

### 1. Get API Token (Hugging Face)

```bash
# Sign up for free account at https://huggingface.co/
# Generate token at https://huggingface.co/settings/tokens
# Create Read token (User Access Token with "Read" permission)
```

### 2. Configure Environment

```bash
# Add to your .env file
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

### 3. Install Dependencies

```bash
# Already included in requirements.txt
pip install requests
```

## Usage

### Via API

Analyze auction images programmatically:

```bash
# Analyze auction images
curl -X POST http://localhost:5000/api/auctions/{auction_id}/analyze-images \
  -H "Content-Type: application/json" \
  -d '{"provider": "huggingface"}' \
  --cookie "session=your-session-cookie"
```

Response:
```json
{
  "success": true,
  "message": "Images analyzed successfully",
  "analysis": {
    "description": "a storage unit filled with boxes and furniture",
    "fullness_rating": 75,
    "items": ["boxes", "furniture", "chair", "table"],
    "categories": ["furniture", "boxes/containers"],
    "condition": "full",
    "valuable_items": true,
    "images_analyzed": 1,
    "total_images": 3
  }
}
```

### Via Admin Interface

1. Log in as admin user
2. View auction detail page
3. Click "🤖 Analyze Images with AI" button in Admin Tools
4. Wait for analysis (5-30 seconds depending on provider)
5. Results saved to auction automatically

### Via Python

```python
from image_analysis import ImageAnalysisService

# Initialize analyzer
analyzer = ImageAnalysisService(provider='huggingface')

# Analyze images
image_urls = ['https://example.com/unit1.jpg', 'https://example.com/unit2.jpg']
result = analyzer.analyze_multiple_images(image_urls)

print(f"Description: {result['description']}")
print(f"Fullness: {result['fullness_rating']}%")
print(f"Items: {', '.join(result['items'])}")
print(f"Valuable: {result['valuable_items']}")
```

## Switching Providers

The system is designed for easy provider swapping:

### Add OpenAI GPT-4 Vision (Future)

```python
# In image_analysis.py, implement OpenAIVisionAnalyzer.analyze_image()
# Then use it:
analyzer = ImageAnalysisService(provider='openai')
```

### Add Claude Vision (Future)

```python
# In image_analysis.py, implement ClaudeVisionAnalyzer.analyze_image()
# Then use it:
analyzer = ImageAnalysisService(provider='claude')
```

### Create Custom Provider

```python
from image_analysis import ImageAnalyzerBase

class MyCustomAnalyzer(ImageAnalyzerBase):
    def analyze_image(self, image_url: str) -> Dict:
        # Your custom implementation
        return {
            'description': 'Custom analysis',
            'fullness_rating': 50,
            'items': [],
            'categories': [],
            'condition': 'unknown',
            'valuable_items': False
        }

# Register in ImageAnalysisService._create_analyzer()
```

## Database Schema

Analysis results are stored in the `auctions` table:

```sql
ai_description TEXT,        -- Generated description
fullness_rating INTEGER,    -- 0-100 percentage
```

## Frontend Display

- **Auction Cards**: Show fullness rating as progress bar with percentage
- **Detail View**: Display full AI description in blue info box
- **Admin Tools**: Button to trigger re-analysis

## Performance

### Hugging Face
- First request: ~10-30 seconds (cold start)
- Subsequent requests: ~3-5 seconds
- Rate limit: ~1000 requests/day (free tier)

### Best Practices

1. **Analyze once per auction**: Don't re-analyze unless images change
2. **Batch processing**: Use background jobs for bulk analysis
3. **Cache results**: Results are stored in database
4. **Error handling**: Gracefully handle API failures

## Troubleshooting

### "Model is loading" Error

Hugging Face models have cold starts. Wait 20 seconds and retry.

### Rate Limit Exceeded

Free tier has limits. Consider:
- Upgrading to paid tier
- Switching to OpenAI/Claude for production
- Implementing request throttling

### Poor Analysis Quality

BLIP is general-purpose. For better results:
- Switch to GPT-4 Vision or Claude
- Use images with good lighting
- Ensure images show unit contents clearly

## Cost Comparison

| Provider | Cost per Image | Accuracy | Speed |
|----------|---------------|----------|-------|
| Hugging Face | Free | Good | Slow (cold start) |
| GPT-4 Vision | $0.01-0.03 | Excellent | Fast |
| Claude Vision | $0.01-0.03 | Excellent | Fast |

## Examples

### Empty Unit
```json
{
  "description": "empty storage unit with bare walls",
  "fullness_rating": 10,
  "condition": "empty"
}
```

### Packed Unit
```json
{
  "description": "storage unit completely filled with furniture, boxes, and appliances",
  "fullness_rating": 90,
  "items": ["boxes", "furniture", "refrigerator", "couch", "chairs"],
  "categories": ["furniture", "appliances", "boxes/containers"],
  "condition": "packed",
  "valuable_items": true
}
```

## Future Enhancements

- [ ] Implement GPT-4 Vision analyzer
- [ ] Implement Claude Vision analyzer
- [ ] Multi-image analysis (combine insights from all images)
- [ ] Item detection with bounding boxes
- [ ] Value estimation based on visible items
- [ ] Condition assessment (damaged, pristine, etc.)
- [ ] Background job processing for bulk analysis
- [ ] Webhook notifications when analysis completes
