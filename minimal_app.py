#!/usr/bin/env python3
"""
Absolute minimal Flask app for Railway testing
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello Railway! App is running."

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'port': os.environ.get('PORT', 'not_set')})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)