#!/usr/bin/env python3
"""
Ultra simple HTTP server for Railway testing
"""

import http.server
import socketserver
import os
import json
import threading
import time

PORT = int(os.environ.get('PORT', 8000))

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = '''
            <html>
            <head><title>Railway Test</title></head>
            <body>
                <h1>🚀 Railway Server Working!</h1>
                <p>This is a basic HTTP server running on Railway</p>
                <p>Port: %s</p>
                <p><a href="/health">Health Check</a></p>
            </body>
            </html>
            ''' % PORT
            self.wfile.write(response.encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'server': 'basic_http',
                'port': PORT,
                'railway_env': os.environ.get('RAILWAY_ENVIRONMENT', 'not_set')
            }
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Simple logging
        print(f"REQUEST: {format % args}")

def start_server():
    print(f"Starting basic HTTP server on port {PORT}")
    print(f"Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), SimpleHandler) as httpd:
        print(f"Server running at http://0.0.0.0:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()