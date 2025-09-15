#!/usr/bin/env python3
"""
Simple HTTP server for testing the Retell chat widget locally.
Serves static files with proper headers for iframe embedding.
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to allow iframe embedding
        self.send_header("X-Frame-Options", "ALLOWALL")
        self.send_header("Content-Security-Policy", "frame-ancestors *;")

        # Add CORS headers for development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        super().end_headers()

    def do_GET(self):
        # Serve HTML files with proper content type
        if self.path.endswith(".html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            try:
                with open(self.path[1:], "rb") as f:  # Remove leading slash
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            super().do_GET()


def main():
    PORT = int(os.environ.get("PORT", 8000))

    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Server starting on port {PORT}")
        print(f"📁 Serving files from: {os.getcwd()}")
        print(f"🌐 Local URL: http://localhost:{PORT}/retell-inline-branded.html")
        print(f"🔗 Use ngrok to expose: ngrok http {PORT}")
        print("Press Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
