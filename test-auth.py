#!/usr/bin/env python3
"""
Test script to verify authentication behavior
"""

import os
import sys

print("=== Authentication Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print()

# Check environment variables
username = os.environ.get('RAILWAY_USERNAME')
password = os.environ.get('RAILWAY_PASSWORD')

print("Environment Variables:")
print(f"RAILWAY_USERNAME: {'SET' if username else 'NOT SET'}")
print(f"RAILWAY_PASSWORD: {'SET' if password else 'NOT SET'}")

if username:
    print(f"Username value: {username}")
if password:
    print(f"Password length: {len(password)} characters")

print()

# Test the logic from secure-web-noted.py
if not username or not password:
    print("❌ FAIL: Environment variables missing - app should exit")
    print("This means the app will fail to start, which is correct behavior")
else:
    print("✅ PASS: Environment variables are properly set")
    print("App should start and require authentication")

print()
print("Next steps:")
if not username or not password:
    print("1. Set RAILWAY_USERNAME and RAILWAY_PASSWORD in Railway dashboard")
    print("2. Redeploy the app")
    print("3. Visit the URL - should show login page")
else:
    print("1. Visit https://web-production-875d.up.railway.app/")
    print("2. Should be redirected to login page")
    print("3. Use the credentials you set in Railway")