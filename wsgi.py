#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment with environment variable handling
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def create_app():
    """Create Flask app with proper error handling"""
    try:
        # Import the main Flask app using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_mobile_noted", "web-mobile-noted.py")
        if spec and spec.loader:
            web_mobile_noted = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(web_mobile_noted)
            return web_mobile_noted.app
        else:
            raise ImportError("Could not load web-mobile-noted.py")
    except ValueError as e:
        if "environment variable" in str(e):
            # Create a temporary Flask app to show the error
            from flask import Flask, jsonify
            
            error_app = Flask(__name__)
            
            @error_app.route('/health')
            def health():
                return jsonify({
                    'status': 'error',
                    'message': 'Environment variables not configured',
                    'required_vars': ['NOTED_USERNAME', 'NOTED_PASSWORD_HASH'],
                    'error': str(e)
                }), 500
            
            @error_app.route('/')
            def root():
                return f'''
                <html>
                <head><title>Configuration Required</title></head>
                <body>
                    <h1>🔧 Configuration Required</h1>
                    <p>Please set the following environment variables in Railway:</p>
                    <ul>
                        <li><strong>NOTED_USERNAME</strong>: admin</li>
                        <li><strong>NOTED_PASSWORD_HASH</strong>: [password hash]</li>
                    </ul>
                    <p>Error: {str(e)}</p>
                    <p><a href="/health">Health Check</a></p>
                </body>
                </html>
                '''
            
            return error_app
        else:
            raise
    except Exception as e:
        # Fallback error app for any other issues
        from flask import Flask, jsonify
        
        error_app = Flask(__name__)
        
        @error_app.route('/health')
        def health():
            return jsonify({
                'status': 'error',
                'message': 'Application startup error',
                'error': str(e)
            }), 500
        
        @error_app.route('/')
        def root():
            return f'''
            <html>
            <head><title>Startup Error</title></head>
            <body>
                <h1>🚨 Startup Error</h1>
                <p>Application failed to start: {str(e)}</p>
                <p><a href="/health">Health Check</a></p>
            </body>
            </html>
            '''
        
        return error_app

# Create the application
application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)