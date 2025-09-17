#!/usr/bin/env python3
"""
Minimal test app for Railway debugging
"""

from flask import Flask
import os

# Create the app at module level for Gunicorn
app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>🎉 Railway Connection Test</h1><p>If you see this, the deployment is working!</p>'

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Test app is running', 'port': os.environ.get('PORT', 'not set')}

@app.route('/debug')
def debug():
    return {
        'status': 'debug',
        'port': os.environ.get('PORT', 'not set'),
        'environment': 'railway' if 'RAILWAY_ENVIRONMENT' in os.environ else 'local',
        'python_path': os.getcwd()
    }

# For direct execution (testing)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)