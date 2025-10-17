# GitHub Repository Deployment Options for retell-seamless.html

## Overview
This document outlines approaches for serving `retell-seamless.html` from a GitHub repository, allowing updates to the file via git commits rather than manual server file management.

---

## Option 1: Git Clone + Scheduled Pull ⭐ RECOMMENDED FOR PRODUCTION

### Implementation
```bash
# One-time setup
cd /var/www/retell-widget
git clone <repo-url> .

# Cron job (every 10 minutes)
*/10 * * * * cd /var/www/retell-widget && git pull origin main >> /var/log/retell-update.log 2>&1
```

### Pros
- ✅ Simple and battle-tested approach
- ✅ Works with existing server code (zero modifications)
- ✅ Full control over update frequency
- ✅ Fast serving (files are local)
- ✅ Can pin to specific versions/tags if needed
- ✅ Works offline after initial clone

### Cons
- ⚠️ Update delay based on polling interval (5-15 min typical)
- ⚠️ Requires cron setup
- ⚠️ Manual intervention if merge conflicts occur

### Best For
Production deployments prioritizing stability and control

---

## Option 2: GitHub Webhook + Auto-pull ⚡ BEST FOR REAL-TIME

### Implementation
Add webhook endpoint to `server-production.py`:
```python
def do_POST(self):
    if self.path == "/webhook/github-update":
        # Verify GitHub signature
        signature = self.headers.get('X-Hub-Signature-256')
        if verify_signature(signature, secret):
            subprocess.run(['git', 'pull'], cwd='/path/to/repo')
            self.send_response(200)
        else:
            self.send_response(403)
```

Configure GitHub webhook:
- Payload URL: `https://your-domain.com/webhook/github-update`
- Content type: `application/json`
- Secret: Generate secure token
- Events: Just the push event

### Pros
- ✅ Near real-time updates (seconds after push)
- ✅ No polling overhead
- ✅ Only updates when needed
- ✅ Files still served locally (fast)

### Cons
- ⚠️ Requires server code modification
- ⚠️ Need secure webhook authentication
- ⚠️ Server must be publicly accessible
- ⚠️ Slightly more complex setup

### Best For
Active development with frequent updates

---

## Option 3: Proxy to GitHub Raw Content 🔄 SIMPLEST

### Implementation
Modify `do_GET()` in server:
```python
if self.path == "/" or self.path == "/retell-seamless.html":
    github_url = "https://raw.githubusercontent.com/user/repo/main/retell-seamless.html"
    response = requests.get(github_url)
    self.send_response(200)
    self.send_header("Content-Type", "text/html")
    self.end_headers()
    self.wfile.write(response.content)
```

### Pros
- ✅ Always serves latest version (no caching)
- ✅ No git operations on server
- ✅ Minimal code changes
- ✅ No disk space needed

### Cons
- ⚠️ Depends on GitHub availability (external dependency)
- ⚠️ GitHub rate limits (5000/hour authenticated)
- ⚠️ Slower response times (network latency)
- ⚠️ No offline capability
- ⚠️ Can't easily add post-processing

### Best For
Development/testing environments

---

## Option 4: GitHub Pages + Redirect/iframe 🌐

### Implementation
1. Enable GitHub Pages in repo settings
2. Point to main branch or `/docs` folder
3. Access via: `https://username.github.io/repo-name/retell-seamless.html`
4. Optionally redirect/iframe from your domain

### Pros
- ✅ Zero server management
- ✅ Automatic updates on push
- ✅ Free CDN hosting
- ✅ HTTPS included
- ✅ High availability

### Cons
- ⚠️ Public repo required (unless GitHub Pro)
- ⚠️ Can't customize HTTP headers easily
- ⚠️ iframe may affect postMessage communication
- ⚠️ Less control over deployment

### Best For
Public projects with minimal server requirements

---

## Option 5: GitHub API with Local Cache 💾 HYBRID

### Implementation
```python
def get_file_with_cache():
    cache_file = "/tmp/retell-seamless-cache.html"
    cache_ttl = 300  # 5 minutes
    
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < cache_ttl:
            return open(cache_file, 'rb').read()
    
    # Fetch from GitHub API
    api_url = "https://api.github.com/repos/user/repo/contents/retell-seamless.html"
    response = requests.get(api_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
    content = base64.b64decode(response.json()['content'])
    
    # Update cache
    with open(cache_file, 'wb') as f:
        f.write(content)
    
    return content
```

### Pros
- ✅ Balance of freshness and performance
- ✅ Configurable cache TTL
- ✅ Fallback to cache if GitHub down
- ✅ No git operations needed

### Cons
- ⚠️ API rate limits (60/hour unauth, 5000/hour auth)
- ⚠️ More complex logic
- ⚠️ Still external dependency for updates
- ⚠️ Need to handle API token securely

### Best For
Medium-traffic sites wanting automatic updates with caching

---

## Recommendation Matrix

| Scenario | Recommended Option | Reason |
|----------|-------------------|---------|
| **Production (stable)** | Option 1 (Cron) | Reliable, no external dependencies at runtime |
| **Active development** | Option 2 (Webhook) | Real-time updates on every commit |
| **Quick testing** | Option 3 (Proxy) | Fastest setup, no server changes |
| **Public project** | Option 4 (Pages) | Free, automatic, CDN-backed |
| **High-traffic site** | Option 5 (Cache) | Performance with reasonable freshness |

---

## Current Server Compatibility

Based on `server-production.py`:

**What works today:**
- Lines 156-158: Already serves `retell-seamless.html` as default for `/`
- Security headers (CORS, CSP, X-Frame-Options) are well configured
- Environment-based config supports dev/prod modes

**Considerations:**
1. **CORS/CSP**: Options 3-4 may need header adjustments
2. **File path**: Current code expects local file, Options 1-2-5 maintain this
3. **POST endpoint**: Option 2 requires adding `do_POST()` method
4. **Dependencies**: Options 3-5 need `requests` library

---

## Decision Factors

Ask yourself:

1. **Update frequency?**
   - Rarely (daily/weekly) → Option 1
   - Often (multiple times/day) → Option 2
   - Constantly (testing) → Option 3

2. **GitHub repo visibility?**
   - Private → Options 1, 2, or 5 (with auth)
   - Public → Any option works

3. **Infrastructure control?**
   - Full control → Options 1-2
   - Minimal maintenance → Option 4

4. **Rollback capability needed?**
   - Yes → Option 1 (can checkout specific commits)
   - No → Options 2-5 work

5. **GitHub downtime tolerance?**
   - Must work offline → Options 1, 5 (with cache)
   - Can depend on GitHub → Options 3-4

---

## Next Steps

1. Review your requirements against decision factors
2. Choose an option
3. Test in development environment first
4. Document the deployment process
5. Set up monitoring/alerts for update failures

---

**Document created:** 2025-10-17  
**Related files:** `server-production.py`, `server.py`, `retell-seamless.html`

