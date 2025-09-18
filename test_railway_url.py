"""
Test Railway App URL and OneDrive Endpoints
Find the correct Railway URL and test OneDrive functionality
"""

import requests
import json

# Possible Railway URLs to test
POSSIBLE_URLS = [
    "https://web-mobile-noted-production.up.railway.app",
    "https://mobile-noted-production.up.railway.app", 
    "https://noted-web-production.up.railway.app",
    "https://noted-production.up.railway.app",
    "https://web-noted-production.up.railway.app"
]

def test_railway_urls():
    """Test possible Railway URLs to find the working one."""
    print("🔍 Testing Railway URLs...")
    print("=" * 50)
    
    working_urls = []
    
    for url in POSSIBLE_URLS:
        try:
            print(f"\n🧪 Testing: {url}")
            
            # Test basic connectivity
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Basic connectivity: OK ({response.status_code})")
                
                # Test if it's our app by checking for specific endpoints
                test_endpoints = [
                    "/api/onedrive/auth/simple-check",
                    "/login",
                    "/notes"
                ]
                
                app_score = 0
                for endpoint in test_endpoints:
                    try:
                        test_response = requests.get(f"{url}{endpoint}", timeout=5)
                        if test_response.status_code in [200, 302, 401, 403]:  # Any response means endpoint exists
                            app_score += 1
                            print(f"  ✅ {endpoint}: {test_response.status_code}")
                        else:
                            print(f"  ❌ {endpoint}: {test_response.status_code}")
                    except Exception as e:
                        print(f"  ❌ {endpoint}: {str(e)[:50]}")
                
                if app_score >= 2:  # At least 2 endpoints work
                    working_urls.append((url, app_score))
                    print(f"🎯 Likely working app URL! (Score: {app_score}/3)")
                else:
                    print(f"❓ Possible but uncertain (Score: {app_score}/3)")
                    
            else:
                print(f"❌ Basic connectivity: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed: URL not accessible")
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout: URL too slow to respond")
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
    
    return working_urls

def test_onedrive_endpoints(url):
    """Test OneDrive specific endpoints on a working URL."""
    print(f"\n🔬 Testing OneDrive endpoints on: {url}")
    print("=" * 60)
    
    session = requests.Session()
    
    # Test endpoints that don't require authentication
    test_endpoints = {
        "/api/onedrive/auth/simple-check": "Simple connectivity check",
        "/api/onedrive/debug/flow-status": "Debug flow status", 
        "/notes": "Notes page (should redirect to login)"
    }
    
    for endpoint, description in test_endpoints.items():
        try:
            print(f"\n📍 {description}")
            print(f"   Endpoint: {endpoint}")
            
            response = session.get(f"{url}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    json_data = response.json()
                    print(f"   Response: {json.dumps(json_data, indent=2)[:200]}")
                except:
                    print(f"   Response: {response.text[:100]}")
            else:
                print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🚀 Railway App URL Discovery & OneDrive Test")
    print("=" * 70)
    
    # Find working URLs
    working_urls = test_railway_urls()
    
    if working_urls:
        print(f"\n🎉 Found {len(working_urls)} working URL(s):")
        for url, score in working_urls:
            print(f"  • {url} (Score: {score}/3)")
            
        # Test OneDrive on the best URL
        best_url = max(working_urls, key=lambda x: x[1])[0]
        test_onedrive_endpoints(best_url)
        
        print(f"\n✨ Recommended Railway URL: {best_url}")
    else:
        print("\n❌ No working Railway URLs found!")
        print("The app might be:")
        print("  • Down for maintenance")
        print("  • Using a different URL")
        print("  • Not deployed yet")

if __name__ == "__main__":
    main()