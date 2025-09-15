# Retell Chat Widget Integration - Option B Implementation

This solution implements **Option B** from the chatdash.md analysis: using the official Retell widget with brand-matched styling via Shadow DOM injection.

## 🎯 What This Does

- Uses the **official Retell chat widget** (no fork to maintain)
- Injects custom CSS to match your ChatDash brand identity
- Provides a clean iframe-embeddable chat interface
- Maintains automatic updates from Retell while preserving your visual style

## 📁 Files Overview

```
/Helpware/
├── retell-seamless.html        # ⭐ RECOMMENDED: Seamless loading chat widget
├── retell-inline-branded.html  # Original Option B implementation
├── server.py                   # Development server with permissive headers
├── server-production.py        # 🔒 Production server with security hardening
├── TEXT_README.md             # This documentation
└── chatdash.md                # Original analysis and options
```

## 🚀 Quick Start

### Prerequisites

- Python 3.6+ (for local server)
- ngrok installed (`brew install ngrok` on macOS)
- Retell AI account with:
  - Public API key
  - Chat agent ID

### Step 1: Configure Your Retell Credentials

Edit `retell-seamless.html` (recommended) and replace these placeholders:

```html
data-public-key="YOUR_RETELL_PUBLIC_KEY"
data-agent-id="YOUR_CHAT_AGENT_ID"
```

**Optional customizations:**
- `data-title="Helpware Welcome Agent – Alexei"` - Change the header title
- `data-logo-url="https://yourcdn.com/hw-logo.svg"` - Add your logo URL
- `data-color="#0E121B"` - Adjust the primary color

### Step 2: Start Local Server

```bash
# Navigate to project directory
cd "/Users/nuggylover1210/Projects/Alchemical AI/Helpware"

# Start the development server
python3 server.py
```

You should see:
```
🚀 Server starting on port 8000
📁 Serving files from: /Users/nuggylover1210/Projects/Alchemical AI/Helpware
🌐 Local URL: http://localhost:8000/retell-inline-branded.html
🔗 Use ngrok to expose: ngrok http 8000
Press Ctrl+C to stop the server
```

### Step 3: Test Locally

Open your browser to: `http://localhost:8000/retell-seamless.html`

You should see the chat widget load smoothly with your custom branding and no loading flicker.

### Step 4: Expose with ngrok

In a new terminal window (keep the Python server running):

```bash
# Start ngrok tunnel
ngrok http 8000 --log=stdout
```

ngrok will start and show output like:
```
t=2025-09-14T23:11:12-0400 lvl=info msg="started tunnel" obj=tunnels name=command_line addr=http://localhost:8000 url=https://fdc8a91c9bb8.ngrok.app
```

**Get your public URLs:**
- **Chat Widget**: `https://your-ngrok-url.ngrok.app/retell-seamless.html` ⭐ **RECOMMENDED**
- **Alternative**: `https://your-ngrok-url.ngrok.app/retell-inline-branded.html`
- **Test Page**: `https://your-ngrok-url.ngrok.app/test-iframe.html`

**Quick command to get the current ngrok URL:**
```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print('Public URL:', json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

**Test that ngrok is working:**
```bash
curl -I https://your-ngrok-url.ngrok.app/retell-inline-branded.html
```

You should see a `200 OK` response with the proper headers.

### Step 5: Update Retell Allowlist

1. Go to your Retell dashboard
2. Navigate to Public Keys
3. Add your ngrok domain to the allowlist: `abc123.ngrok-free.app`

## 🎨 Visual Customizations Applied

The implementation includes these brand-matching styles:

### Header Styling
- **White background** with dark text (`#0E121B`)
- **Bold title** (18px, 700 weight)
- **Subtitle**: "Our assistant is here to help" (13px, `#98A2B3`)
- **Hidden minimize/close buttons** (fullscreen iframe experience)

### Message Bubbles
- **Agent messages**: Light gray background (`#EEF2F7`)
- **User messages**: Light blue background (`#D5E2FF`)
- **Rounded corners**: 18px border-radius
- **Dark text**: `#0E121B` for readability

### Layout
- **No FAB button** (hidden since we auto-open)
- **Full iframe coverage** with 20px border-radius
- **Subtle border**: `#E6EAF3`
- **Clean footer**: "Powered by Alchemical AI"

### Navigation
- **Back chevron** replaces hamburger menu icon

## 🔧 Integration with ChatDash

Use this iframe code in ChatDash → Add Custom Menu → Iframe to Embed:

```html
<iframe
  id="retell-chat-iframe"
  src="https://your-ngrok-url.ngrok.app/retell-seamless.html"
  style="width:100%;height:100%;border:none;border-radius:20px;overflow:hidden"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
></iframe>
```

### Back Button Integration

Add this script to your ChatDash page to handle the back button:

```javascript
// Listen for back button messages from Retell widget
window.addEventListener('message', function(event) {
  if (event.data && event.data.action === 'navigateBack' && event.data.source === 'retell-widget') {
    // Navigate back to previous tab/view in ChatDash
    // Example: Switch to another tab
    document.querySelector('[data-tab="voice-chat"]').click();
    // Or: Close the iframe
    // document.getElementById('retell-chat-iframe').style.display = 'none';
  }
});
```

### 🚀 Quick Start Commands

**Terminal 1 - Start the server:**
```bash
cd "/Users/nuggylover1210/Projects/Alchemical AI/Helpware"
python3 server.py
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 8000 --log=stdout
```

**Get your current ngrok URL:**
```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print('Chat Widget URL:', json.load(sys.stdin)['tunnels'][0]['public_url'] + '/retell-seamless.html')"
```

### 🔒 Using Production Server (Recommended for Staging/Production)

For better security, use the production server:

```bash
# Set environment variables
export ENVIRONMENT=production
export ALLOWED_ORIGINS=https://your-chatdash-domain.com
export PORT=8000

# Start production server
python3 server-production.py
```

**Production server features:**
- ✅ **Strict CORS policies** - Only allows specified origins
- ✅ **Security headers** - XSS protection, content type validation
- ✅ **Access logging** - Detailed request logging for monitoring
- ✅ **Rate limiting protection** - Basic path traversal prevention
- ✅ **Environment validation** - Ensures proper configuration

**Restart ngrok if needed:**
```bash
# Stop ngrok
pkill ngrok

# Start new tunnel
ngrok http 8000 --log=stdout
```

## 🛠️ Development Server Features

The included `server.py` provides:

- **Proper iframe headers**: `X-Frame-Options: ALLOWALL`
- **CSP policy**: `frame-ancestors *;` for development
- **CORS headers**: For cross-origin testing
- **Correct MIME types**: `text/html; charset=utf-8` for HTML files
- **Auto port detection**: Uses `PORT` environment variable or defaults to 8000

## 🔒 Security Considerations & Production Readiness

### Current Development Setup ⚠️
The current setup is optimized for **development and testing** with permissive security settings:

- **Permissive CORS**: `Access-Control-Allow-Origin: *`
- **Open iframe policy**: `X-Frame-Options: ALLOWALL`
- **Broad CSP**: `frame-ancestors *;`
- **HTTP + ngrok**: Temporary HTTPS via ngrok tunnel
- **No authentication**: Direct access to all endpoints

### 🚨 Critical Security TODOs for Production

#### 1. **HTTPS & SSL Certificates**
```bash
# Option A: Use Let's Encrypt (recommended)
sudo certbot --nginx -d your-domain.com

# Option B: Use Cloudflare for SSL termination
# Configure Cloudflare proxy with Full SSL mode
```

#### 2. **Restrict CORS Origins**
Update `server.py` for production:
```python
# Replace this development setting:
self.send_header("Access-Control-Allow-Origin", "*")

# With your actual ChatDash domain:
self.send_header("Access-Control-Allow-Origin", "https://your-chatdash-domain.com")
```

#### 3. **Harden Content Security Policy**
```python
# Development (current):
self.send_header("Content-Security-Policy", "frame-ancestors *;")

# Production (recommended):
csp = (
    "frame-ancestors https://your-chatdash-domain.com; "
    "default-src 'self' https://dashboard.retellai.com; "
    "script-src 'self' 'unsafe-inline' https://dashboard.retellai.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://dashboard.retellai.com wss://dashboard.retellai.com;"
)
self.send_header("Content-Security-Policy", csp)
```

#### 4. **Add Security Headers**
```python
# Add these headers to server.py:
self.send_header("X-Content-Type-Options", "nosniff")
self.send_header("X-XSS-Protection", "1; mode=block")
self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
self.send_header("Permissions-Policy", "microphone=(), camera=(), geolocation=()")
```

#### 5. **Environment-Based Configuration**
```python
import os

# Use environment variables for security settings
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://your-domain.com').split(',')
DEVELOPMENT = os.getenv('ENVIRONMENT', 'production') == 'development'

if DEVELOPMENT:
    # Permissive settings for development
    self.send_header("Access-Control-Allow-Origin", "*")
else:
    # Strict settings for production
    origin = self.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        self.send_header("Access-Control-Allow-Origin", origin)
```

### 🛡️ Production Deployment Checklist

#### Infrastructure Security
- [ ] **Deploy behind reverse proxy** (nginx/Apache)
- [ ] **Use proper SSL certificates** (Let's Encrypt/commercial)
- [ ] **Configure firewall rules** (only allow 80/443)
- [ ] **Enable fail2ban** or similar intrusion prevention
- [ ] **Set up monitoring** (uptime, security logs)

#### Application Security
- [ ] **Update CORS origins** to specific domains
- [ ] **Implement rate limiting** (nginx limit_req)
- [ ] **Add request logging** for security auditing
- [ ] **Validate all inputs** (though minimal in this case)
- [ ] **Remove debug endpoints** and verbose error messages

#### Retell-Specific Security
- [ ] **Restrict Retell Public Key domains** to production only
- [ ] **Use separate Retell keys** for dev/staging/prod
- [ ] **Monitor Retell API usage** for anomalies
- [ ] **Implement webhook validation** if using Retell webhooks

#### Monitoring & Maintenance
- [ ] **Set up SSL certificate renewal** (automated)
- [ ] **Monitor security headers** (securityheaders.com)
- [ ] **Regular dependency updates** (Python, ngrok alternatives)
- [ ] **Log analysis** for suspicious activity

### 🚀 Production Deployment Options

#### Option 1: Traditional VPS/Cloud Server
```bash
# 1. Set up server (Ubuntu/CentOS)
sudo apt update && sudo apt install nginx python3 python3-pip certbot

# 2. Configure nginx reverse proxy
sudo nano /etc/nginx/sites-available/retell-chat

# 3. Get SSL certificate
sudo certbot --nginx -d your-domain.com

# 4. Deploy application with systemd service
sudo systemctl enable retell-chat.service
```

#### Option 2: Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY server.py retell-seamless.html ./
EXPOSE 8000
CMD ["python3", "server.py"]
```

#### Option 3: Serverless (AWS Lambda/Vercel)
- Deploy static HTML to CDN
- Use serverless functions for dynamic content
- Automatic HTTPS and scaling

### 🔐 Additional Security Recommendations

#### 1. **API Key Management**
```bash
# Use environment variables, never hardcode
export RETELL_PUBLIC_KEY="key_your_actual_key"
export RETELL_AGENT_ID="agent_your_actual_id"
```

#### 2. **Content Validation**
```python
# Validate Retell responses if processing them
import re

def validate_retell_response(data):
    # Sanitize any user-generated content
    if 'message' in data:
        data['message'] = re.sub(r'<script.*?</script>', '', data['message'])
    return data
```

#### 3. **Access Logging**
```python
import logging

# Set up security logging
logging.basicConfig(
    filename='/var/log/retell-chat/security.log',
    format='%(asctime)s - %(remote_addr)s - %(message)s'
)
```

### 🚨 Security Incident Response

If you suspect a security issue:

1. **Immediate Actions**:
   - Rotate Retell API keys
   - Check access logs for suspicious activity
   - Temporarily restrict access if needed

2. **Investigation**:
   - Review server logs
   - Check Retell dashboard for unusual usage
   - Verify SSL certificate validity

3. **Recovery**:
   - Update security configurations
   - Apply patches/updates
   - Monitor for continued issues

## 🚨 Troubleshooting

### Widget Not Loading
1. **Check console errors** in browser dev tools
2. **Verify Retell credentials** are correct
3. **Confirm domain allowlist** includes your ngrok URL
4. **Test direct access** to the HTML file first

### Styling Not Applied
1. **Check Shadow DOM** - styles inject after widget loads
2. **Verify selectors** match Retell's current DOM structure
3. **Increase timeout** in the patcher if needed (currently 8 seconds)

### iframe Issues
1. **Check X-Frame-Options** headers
2. **Verify HTTPS** (required for many iframe features)
3. **Test CSP policies** aren't blocking the embed

### ngrok Connection Issues
1. **Restart ngrok** if tunnel disconnects
2. **Update Retell allowlist** with new ngrok URL
3. **Check firewall** isn't blocking port 8000

**Common ngrok commands:**
```bash
# Check if ngrok is running
curl -s http://localhost:4040/api/tunnels

# Get current public URL
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"

# Test your ngrok URL
curl -I https://your-ngrok-url.ngrok.app/retell-inline-branded.html

# Kill all ngrok processes
pkill ngrok
```

**ngrok URL format:** `https://[random-string].ngrok.app`
- Example: `https://fdc8a91c9bb8.ngrok.app/retell-inline-branded.html`
- Changes each time you restart ngrok
- Always update your Retell allowlist with the new domain

## 📈 Next Steps

### For Production
1. **Deploy to your domain** (replace ngrok)
2. **Update Retell allowlist** with production domain
3. **Implement proper CSP** headers
4. **Add monitoring/logging** as needed

### Customization Options
1. **Modify colors** in the CSS injection block
2. **Change header text** via data attributes
3. **Add your logo** with `data-logo-url`
4. **Adjust dimensions** for different iframe sizes

## 🔄 Maintenance

This solution uses the **official Retell widget**, so:
- ✅ **Automatic updates** from Retell
- ✅ **No fork maintenance** required
- ✅ **Latest features** included automatically
- ⚠️ **CSS selectors** may need updates if Retell changes their DOM structure

## 📞 Support

If you encounter issues:
1. Check the browser console for errors
2. Verify all credentials and allowlists
3. Test with the default widget first (Option A) to isolate styling issues
4. Review the original `chatdash.md` for alternative approaches

---

**Implementation Status**: ✅ Complete and ready for testing
**Last Updated**: September 15, 2025
