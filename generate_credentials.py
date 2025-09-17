#!/usr/bin/env python3
"""
Generate secure credentials for Web Mobile Noted
Run this script to generate SECRET_KEY and PASSWORD_HASH for Railway deployment
"""

import secrets
from werkzeug.security import generate_password_hash
import getpass

def generate_secret_key():
    """Generate a cryptographically secure secret key"""
    return secrets.token_hex(32)

def generate_password_hash_interactive():
    """Generate password hash with user input"""
    print("🔐 Generate Password Hash")
    print("Enter a strong password for your notes app:")
    
    while True:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords don't match. Please try again.")
            continue
            
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long.")
            continue
            
        break
    
    return generate_password_hash(password)

def main():
    print("🛡️  Web Mobile Noted - Security Credential Generator")
    print("=" * 60)
    
    # Generate secret key
    print("\n1. Generating SECRET_KEY...")
    secret_key = generate_secret_key()
    print(f"✅ SECRET_KEY: {secret_key}")
    
    # Generate password hash
    print("\n2. Generating PASSWORD_HASH...")
    password_hash = generate_password_hash_interactive()
    print(f"✅ PASSWORD_HASH: {password_hash}")
    
    # Display Railway instructions
    print("\n" + "=" * 60)
    print("🚀 Railway Environment Variables")
    print("=" * 60)
    print("Copy these to your Railway project settings:")
    print()
    print(f"SECRET_KEY={secret_key}")
    print("NOTED_USERNAME=admin")  # User can change this
    print(f"NOTED_PASSWORD_HASH={password_hash}")
    print("FLASK_ENV=production")
    print()
    print("📝 Optional: Change NOTED_USERNAME to your preferred username")
    print("🔗 Railway Settings: https://railway.app/project/<your-project>/settings")
    print()
    print("✅ Security features enabled:")
    print("   - Authentication required")
    print("   - Rate limiting (100/hour, 20/min)")
    print("   - CSRF protection")
    print("   - Security headers")
    print("   - Session management")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")