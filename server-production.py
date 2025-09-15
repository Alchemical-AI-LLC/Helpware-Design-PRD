#!/usr/bin/env python3
"""
Production-ready HTTP server for Retell Chat Widget
Includes proper security headers, environment-based configuration, and logging.
"""

import http.server
import socketserver
import os
import sys
import logging
from urllib.parse import urlparse
from datetime import datetime


class ProductionHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Production HTTP request handler with security hardening
    """

    def __init__(self, *args, **kwargs):
        # Load environment configuration
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.is_development = self.environment == "development"

        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Enhanced logging with security information"""
        client_ip = self.client_address[0]
        user_agent = self.headers.get("User-Agent", "Unknown")
        referer = self.headers.get("Referer", "None")

        log_entry = f"{datetime.now().isoformat()} - {client_ip} - {format % args} - UA: {user_agent} - Ref: {referer}"

        # Log to file in production
        if not self.is_development:
            logging.info(log_entry)
        else:
            print(log_entry)

    def end_headers(self):
        """Add comprehensive security headers"""

        # CORS Configuration
        origin = self.headers.get("Origin")
        if self.is_development:
            # Permissive for development
            self.send_header("Access-Control-Allow-Origin", "*")
        else:
            # Strict for production
            if origin and origin in self.allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
            elif len(self.allowed_origins) == 1 and self.allowed_origins[0]:
                self.send_header("Access-Control-Allow-Origin", self.allowed_origins[0])

        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")  # 24 hours

        # Frame Options
        if self.is_development:
            self.send_header("X-Frame-Options", "ALLOWALL")
        else:
            # Allow framing only from allowed origins
            if self.allowed_origins and self.allowed_origins[0]:
                self.send_header(
                    "X-Frame-Options", f"ALLOW-FROM {self.allowed_origins[0]}"
                )
            else:
                self.send_header("X-Frame-Options", "SAMEORIGIN")

        # Content Security Policy
        if self.is_development:
            csp = "frame-ancestors *;"
        else:
            # Strict CSP for production
            frame_ancestors = (
                " ".join(self.allowed_origins) if self.allowed_origins[0] else "'self'"
            )
            csp = (
                f"frame-ancestors {frame_ancestors}; "
                "default-src 'self' https://dashboard.retellai.com; "
                "script-src 'self' 'unsafe-inline' https://dashboard.retellai.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://dashboard.retellai.com wss://dashboard.retellai.com; "
                "font-src 'self' data:; "
                "media-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self';"
            )

        self.send_header("Content-Security-Policy", csp)

        # Additional Security Headers
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Permitted-Cross-Domain-Policies", "none")

        # Permissions Policy (restrict sensitive features)
        permissions = (
            "microphone=(), "
            "camera=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        self.send_header("Permissions-Policy", permissions)

        # Cache Control
        if self.path.endswith(".html"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header(
                "Cache-Control", "public, max-age=3600"
            )  # 1 hour for assets

        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests with security validation"""

        # Security: Block access to sensitive files
        blocked_patterns = [".py", ".env", ".git", ".log", "server-production"]
        if any(pattern in self.path for pattern in blocked_patterns):
            self.send_error(403, "Access Forbidden")
            return

        # Rate limiting check (basic implementation)
        client_ip = self.client_address[0]
        if not self.is_development:
            # In production, you'd implement proper rate limiting here
            # For now, just log suspicious activity
            if self.path.count("../") > 0:
                logging.warning(f"Path traversal attempt from {client_ip}: {self.path}")
                self.send_error(400, "Bad Request")
                return

        # Serve HTML files with proper content type
        if self.path.endswith(".html") or self.path == "/":
            try:
                # Default to retell-seamless.html for root requests
                file_path = (
                    "retell-seamless.html" if self.path == "/" else self.path[1:]
                )

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())

            except FileNotFoundError:
                self.send_error(404, "File not found")
            except Exception as e:
                if not self.is_development:
                    logging.error(f"Server error: {e}")
                    self.send_error(500, "Internal Server Error")
                else:
                    self.send_error(500, f"Internal Server Error: {e}")
        else:
            # Handle other file types (CSS, JS, images, etc.)
            super().do_GET()

    def version_string(self):
        """Hide server version for security"""
        return "RetellChatServer/1.0"


def setup_logging():
    """Configure logging for production"""
    log_dir = "/var/log/retell-chat"
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except PermissionError:
            log_dir = "./logs"
            os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/access.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def validate_environment():
    """Validate environment configuration"""
    environment = os.getenv("ENVIRONMENT", "production")

    if environment == "production":
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if not allowed_origins:
            print("⚠️  WARNING: ALLOWED_ORIGINS not set for production environment")
            print("   Set ALLOWED_ORIGINS=https://your-chatdash-domain.com")
            return False

        # Validate HTTPS origins in production
        origins = allowed_origins.split(",")
        for origin in origins:
            if origin and not origin.startswith("https://"):
                print(f"⚠️  WARNING: Non-HTTPS origin in production: {origin}")
                print("   All origins should use HTTPS in production")
                return False

    return True


def main():
    """Main server function"""

    # Environment validation
    if not validate_environment():
        print("❌ Environment validation failed")
        sys.exit(1)

    # Setup logging
    environment = os.getenv("ENVIRONMENT", "production")
    if environment == "production":
        setup_logging()

    # Server configuration
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces in production

    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start server
    with socketserver.TCPServer((HOST, PORT), ProductionHTTPRequestHandler) as httpd:
        print(f"🚀 Retell Chat Server starting")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🌐 Server URL: http://{HOST}:{PORT}")
        print(f"🔒 Environment: {environment}")

        if environment == "development":
            print(f"🔗 Use ngrok to expose: ngrok http {PORT}")
            print("⚠️  Development mode - permissive security settings")
        else:
            print("🛡️  Production mode - security hardened")
            allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
            if allowed_origins:
                print(f"✅ Allowed origins: {allowed_origins}")

        print("Press Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
