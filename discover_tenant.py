#!/usr/bin/env python3
"""
Try to discover the tenant ID for Hayden Beverage organization.
"""

import requests
import json

def discover_tenant():
    print("=== Attempting to discover tenant information ===")
    
    # Try to discover tenant through common endpoints
    domain = "haydenbeverage.com"  # Common domain pattern
    
    # Method 1: Try OpenID configuration endpoint
    try:
        print(f"\n1. Trying to discover tenant for domain: {domain}")
        
        # This endpoint can help discover tenant info for a domain
        discovery_url = f"https://login.microsoftonline.com/{domain}/v2.0/.well-known/openid_configuration"
        response = requests.get(discovery_url, timeout=10)
        
        if response.status_code == 200:
            config = response.json()
            issuer = config.get('issuer', '')
            if 'microsoftonline.com' in issuer:
                # Extract tenant ID from issuer URL
                tenant_id = issuer.split('/')[-2] if '/' in issuer else None
                if tenant_id:
                    print(f"   ✅ Found tenant ID: {tenant_id}")
                    return tenant_id
        else:
            print(f"   ❌ Discovery failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception during discovery: {e}")
    
    # Method 2: Try alternative domains
    alternative_domains = [
        "haydenbeverage.onmicrosoft.com",
        "hayden.com",
        "haydenbev.com"
    ]
    
    for alt_domain in alternative_domains:
        try:
            print(f"\n2. Trying alternative domain: {alt_domain}")
            discovery_url = f"https://login.microsoftonline.com/{alt_domain}/v2.0/.well-known/openid_configuration"
            response = requests.get(discovery_url, timeout=10)
            
            if response.status_code == 200:
                config = response.json()
                issuer = config.get('issuer', '')
                if 'microsoftonline.com' in issuer:
                    tenant_id = issuer.split('/')[-2] if '/' in issuer else None
                    if tenant_id:
                        print(f"   ✅ Found tenant ID via {alt_domain}: {tenant_id}")
                        return tenant_id
            else:
                print(f"   ❌ Discovery failed for {alt_domain}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception for {alt_domain}: {e}")
    
    print("\n❌ Could not discover tenant automatically")
    print("\n🔍 Manual steps to find your tenant ID:")
    print("1. Go to https://portal.azure.com")
    print("2. Sign in with your Hayden Beverage account") 
    print("3. Go to 'Azure Active Directory' or 'Microsoft Entra ID'")
    print("4. Look for 'Tenant ID' in the overview section")
    print("5. Copy the tenant ID (GUID format)")
    
    return None

if __name__ == "__main__":
    tenant_id = discover_tenant()
    
    if tenant_id:
        print(f"\n✅ Use this authority in your OneDrive manager:")
        print(f"   AUTHORITY = \"https://login.microsoftonline.com/{tenant_id}\"")
    else:
        print(f"\n⚠️  You'll need to manually find your tenant ID and update the authority.")