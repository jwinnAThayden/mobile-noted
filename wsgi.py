#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment
This ensures proper application startup in production
"""

import os
import sys
import importlib.util
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import the Flask application (handle hyphenated filename)
    module_path = os.path.join(current_dir, "web-mobile-noted.py")
    logger.info(f"Loading module from: {module_path}")
    
    spec = importlib.util.spec_from_file_location("web_mobile_noted", module_path)
    web_mobile_noted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_mobile_noted)

    app = web_mobile_noted.app
    logger.info("✅ Flask application loaded successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to load Flask application: {e}")
    raise

# This is what Gunicorn will use
application = app

# This is what Gunicorn will use
application = app

if __name__ == "__main__":
    # For direct execution (fallback)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)