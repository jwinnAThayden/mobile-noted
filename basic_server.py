#!/usr/bin/env python3
"""
Basic HTTP server test for Railway
"""

import http.server
import socketserver
import os
import json
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get('PORT', 8000))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Hello Railway! Basic server is running.')
            
        elif parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'ok', 'port': PORT}
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_error(404)

if __name__ == "__main__":
    print(f"Starting basic HTTP server on port {PORT}")
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server running at http://0.0.0.0:{PORT}")
        httpd.serve_forever()