#!/usr/bin/env python3
import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def hello():
    port = os.environ.get('PORT', 'not set')
    logger.info(f"Request received on port {port}")
    return f'🎉 Hello Railway! Working on port {port}'

@app.route('/health')
def health():
    return {
        'status': 'ok', 
        'port': os.environ.get('PORT', 'not set'),
        'message': 'App is healthy and responding!'
    }

@app.route('/test')
def test():
    return 'Test endpoint working! ✅'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # For Gunicorn
    port = os.environ.get('PORT', 'unknown')
    logger.info(f"Running under Gunicorn, PORT={port}")

# Log all environment variables for debugging
logger.info("Environment variables:")
for key, value in os.environ.items():
    if 'PORT' in key or 'RAILWAY' in key:
        logger.info(f"{key}={value}")