#!/usr/bin/env python3
"""
Diagnostic version of the web app to check environment variables
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/diagnostic')
def diagnostic():
    """Diagnostic endpoint to check environment variables"""
    return jsonify({
        'python_version': sys.version,
        'railway_username_set': bool(os.environ.get('RAILWAY_USERNAME')),
        'railway_password_set': bool(os.environ.get('RAILWAY_PASSWORD')),
        'username_length': len(os.environ.get('RAILWAY_USERNAME', '')),
        'password_length': len(os.environ.get('RAILWAY_PASSWORD', '')),
        'all_env_vars': list(os.environ.keys()),
        'working_directory': os.getcwd()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return "OK", 200

@app.route('/')
def index():
    """Simple index showing environment status"""
    username = os.environ.get('RAILWAY_USERNAME')
    password = os.environ.get('RAILWAY_PASSWORD')
    
    status = "Environment variables are "
    if username and password:
        status += "PROPERLY SET ✅"
    else:
        status += "MISSING ❌"
    
    return f"""
    <html>
        <head><title>Diagnostic Check</title></head>
        <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
            <h1>🔍 Railway Environment Diagnostic</h1>
            <h2>{status}</h2>
            <p><strong>RAILWAY_USERNAME:</strong> {'SET' if username else 'NOT SET'}</p>
            <p><strong>RAILWAY_PASSWORD:</strong> {'SET' if password else 'NOT SET'}</p>
            <hr>
            <p><a href="/diagnostic">View JSON Diagnostic</a></p>
            <p><a href="/health">Health Check</a></p>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))