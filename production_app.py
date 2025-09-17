#!/usr/bin/env python3
"""
Production-ready app entry point that handles missing environment variables gracefully
"""

import os
import sys

def create_app():
    """Create Flask app with proper error handling"""
    try:
        # Try to import and create the main app
        from app import app
        return app
    except ValueError as e:
        if "environment variable" in str(e):
            # Create a minimal Flask app to show environment variable error
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
                return jsonify({
                    'status': 'error',
                    'message': 'Please configure environment variables',
                    'required_vars': ['NOTED_USERNAME', 'NOTED_PASSWORD_HASH']
                }), 500
            
            return error_app
        else:
            raise

# Create the application
application = create_app()
app = application  # Alias for compatibility

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)