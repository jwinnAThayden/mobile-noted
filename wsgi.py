#!/usr/bin/env python3
"""
Simple WSGI entry point for Railway deployment
"""

from app import app

# This is what Gunicorn will use
application = app

if __name__ == "__main__":
    # For direct execution (fallback)
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)