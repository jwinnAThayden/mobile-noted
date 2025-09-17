#!/usr/bin/env python3
"""
Debug version of Web Mobile Noted - minimal Flask app for Railway testing
"""

from flask import Flask, jsonify
import os
import sys
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'Web Mobile Noted Debug',
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version
    })

@app.route('/env-check')
def env_check():
    """Check environment variables"""
    return jsonify({
        'environment_vars': {
            'PORT': os.environ.get('PORT'),
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'NOTED_USERNAME': 'SET' if os.environ.get('NOTED_USERNAME') else 'NOT_SET',
            'NOTED_PASSWORD_HASH': 'SET' if os.environ.get('NOTED_PASSWORD_HASH') else 'NOT_SET',
            'SECRET_KEY': 'SET' if os.environ.get('SECRET_KEY') else 'GENERATED'
        },
        'all_env_vars': {k: 'SET' if v else 'NOT_SET' for k, v in os.environ.items() if 'NOTED' in k or k in ['PORT', 'RAILWAY_ENVIRONMENT']}
    })

@app.route('/')
def index():
    """Simple index"""
    return jsonify({
        'message': 'Debug app is running',
        'check_endpoints': ['/health', '/env-check']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🔍 Starting debug app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)