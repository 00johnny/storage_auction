# HTTP Basic Authentication Setup

## Overview
HTTP Basic Auth provides a simple way to password-protect the entire site during testing/staging. This prevents unauthorized access before the site is ready for public use.

## Quick Setup

### 1. Create/Update Your `.env` File

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
nano .env
```

### 2. Enable Basic Auth

In your `.env` file, set:

```bash
ENABLE_BASIC_AUTH=true
BASIC_AUTH_USERNAME=your_username
BASIC_AUTH_PASSWORD=your_secure_password
```

### 3. Restart the Flask Server

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python3 api_backend.py
```

## How It Works

When enabled:
- **ALL routes** require HTTP Basic Auth credentials
- Users will see a browser login prompt
- Applies to: main site, admin portal, API endpoints, static files
- Session persists per browser session

## Testing

1. Visit your site: `http://your-domain.com`
2. Browser will prompt for username/password
3. Enter credentials from your `.env` file
4. Site will be accessible for that browser session

## Disable Basic Auth

To disable (for production with proper user authentication):

```bash
# In .env file:
ENABLE_BASIC_AUTH=false
```

Or simply remove/comment out the line.

## Security Notes

- ⚠️ **NOT for production!** Use the built-in user authentication system instead
- ✅ **Perfect for:** Testing, staging, development environments
- 🔒 **HTTPS recommended:** Basic Auth sends credentials in base64 (not encrypted)
- 🎯 **Use case:** "Quick and dirty" protection while building/testing

## Production Security

For production, disable Basic Auth and use:
- Built-in user authentication (login system)
- Role-based access control (admin, power, regular)
- HTTPS/SSL certificates
- Proper session management

## Troubleshooting

**Q: I'm getting repeated login prompts**
A: Check that your credentials in `.env` match what you're entering

**Q: How do I log out?**
A: Close all browser windows or clear browser credentials

**Q: Does this work with the API?**
A: Yes, API clients need to send Basic Auth headers

**Q: Can I use different credentials for different users?**
A: No, this is single-user protection. For multi-user, use the built-in user system.

## API Usage with Basic Auth

When making API calls with Basic Auth enabled:

```bash
# Using curl
curl -u username:password http://your-domain.com/api/auctions

# Using fetch in JavaScript
fetch('http://your-domain.com/api/auctions', {
  headers: {
    'Authorization': 'Basic ' + btoa('username:password')
  }
})
```
