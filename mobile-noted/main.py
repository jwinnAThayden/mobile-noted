#!/usr/bin/env python3
"""
Main entry point for Mobile Noted Android app
"""

# Import and run the mobile noted app
if __name__ == '__main__':
    # Import from the mobile-noted.py file (with dash, so we use importlib)
    import importlib.util
    import sys
    import os
    
    # Load the mobile-noted.py module
    module_path = os.path.join(os.path.dirname(__file__), "mobile-noted.py")
    spec = importlib.util.spec_from_file_location("mobile_noted", module_path)
    
    if spec is None or spec.loader is None:
        raise ImportError("Could not load mobile-noted.py module")
    
    mobile_noted = importlib.util.module_from_spec(spec)
    sys.modules["mobile_noted"] = mobile_noted
    spec.loader.exec_module(mobile_noted)
    
    # Run the app
    app = mobile_noted.MobileNotedApp()
    app.run()
