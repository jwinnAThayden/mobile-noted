#!/usr/bin/env python3
"""
Password Hash Generator for Web Mobile Noted
Generate secure password hashes for Railway environment variables
"""

from werkzeug.security import generate_password_hash
import getpass

def main():
    print("🔐 Web Mobile Noted - Password Hash Generator")
    print("=" * 50)
    
    # Get username
    username = input("Enter new username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    # Get password (hidden input)
    password = getpass.getpass("Enter new password: ")
    if not password:
        print("❌ Password cannot be empty!")
        return
    
    # Confirm password
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords don't match!")
        return
    
    # Generate hash
    password_hash = generate_password_hash(password)
    
    print("\n✅ Password hash generated successfully!")
    print("\n📋 Railway Environment Variables:")
    print("=" * 50)
    print(f"NOTED_USERNAME={username}")
    print(f"NOTED_PASSWORD_HASH={password_hash}")
    
    print("\n🚀 Instructions:")
    print("1. Copy the variables above")
    print("2. Go to your Railway project dashboard")
    print("3. Navigate to Variables tab")
    print("4. Add both environment variables")
    print("5. Redeploy your application")
    
    print("\n🔒 Security Note:")
    print("- Your password is hashed using Werkzeug's secure hash function")
    print("- The original password is never stored")
    print("- Keep your Railway environment variables secure")

if __name__ == "__main__":
    main()