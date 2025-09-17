#!/usr/bin/env python3
"""
Main entry point for Web Mobile Noted application
This file is used by deployment platforms like Railway
"""

import os
from web_mobile_noted import app

if __name__ == '__main__':
    # Get port from environment variable (for cloud hosting) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print("🌐 Starting Web Mobile Noted...")
    print("📱 Access on mobile: http://your-ip-address:" + str(port))
    print("💻 Access on desktop: http://localhost:" + str(port))
    print("🔧 To stop: Press Ctrl+C")
    
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production