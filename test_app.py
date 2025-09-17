#!/usr/bin/env python3
"""
Minimal test app for Railway debugging
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>🎉 Railway Connection Test</h1><p>If you see this, the deployment is working!</p>'

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Test app is running'}

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)