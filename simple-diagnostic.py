#!/usr/bin/env python3
"""
Ultra-simple diagnostic to check what's happening on Railway
"""

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    username = os.environ.get('RAILWAY_USERNAME')
    password = os.environ.get('RAILWAY_PASSWORD')
    
    result = f"""
RAILWAY ENVIRONMENT CHECK
========================

RAILWAY_USERNAME: {username or 'NOT SET'}
RAILWAY_PASSWORD: {password or 'NOT SET'}

Status: {'VARIABLES CONFIGURED' if username and password else 'VARIABLES MISSING'}

If variables are MISSING:
1. Go to Railway Dashboard
2. Select your project  
3. Go to Variables tab
4. Add RAILWAY_USERNAME and RAILWAY_PASSWORD
5. Redeploy

If variables are CONFIGURED:
- The secure app should work
- Visit /switch-to-secure to activate secure version
"""
    
    return f"<pre>{result}</pre>"

@app.route('/switch-to-secure')
def switch_secure():
    return """
<h2>Ready to Switch to Secure Version</h2>
<p>If variables are properly set, I'll switch the Procfile back to secure-web-noted.py</p>
<p>The secure app will then require login for all access.</p>
"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))