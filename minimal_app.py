#!/usr/bin/env python3
"""
Absolute minimal Flask app for Railway testing
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

print(f"Starting minimal app on port {os.environ.get('PORT', 5000)}", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)

@app.route('/')
def home():
    print("Root endpoint accessed", file=sys.stderr)
    return "Hello Railway! App is running."

@app.route('/health')
def health():
    print("Health endpoint accessed", file=sys.stderr)
    return jsonify({'status': 'ok', 'port': os.environ.get('PORT', 'not_set')})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Binding to 0.0.0.0:{port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=False)