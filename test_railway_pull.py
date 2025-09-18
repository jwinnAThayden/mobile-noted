"""
Test Railway OneDrive Pull Functionality
Test the specific pull mechanism to see why notes aren't syncing
"""

import requests
import json
from datetime import datetime

# Correct Railway URL found from previous test
RAILWAY_URL = "https://mobile-noted-production.up.railway.app"

def test_railway_onedrive_pull():
    """Test the Railway OneDrive pull functionality step by step."""
    print("🧪 Railway OneDrive Pull Test")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Check authentication status
    print("\n1️⃣ Checking OneDrive authentication...")
    try:
        auth_response = session.get(f"{RAILWAY_URL}/api/onedrive/auth/simple-check")
        auth_data = auth_response.json()
        print(f"   Status: {auth_response.status_code}")
        print(f"   Authenticated: {auth_data.get('authenticated', False)}")
        
        if not auth_data.get('authenticated', False):
            print("   ❌ Not authenticated - need to authenticate first")
            return
        else:
            print("   ✅ Authentication confirmed")
            
    except Exception as e:
        print(f"   ❌ Auth check failed: {e}")
        return
    
    # Step 2: Test list notes endpoint
    print("\n2️⃣ Testing list OneDrive notes...")
    try:
        # Need to login first to get session
        login_response = session.get(f"{RAILWAY_URL}/login")
        print(f"   Login page status: {login_response.status_code}")
        
        # Try the list notes endpoint
        list_response = session.get(f"{RAILWAY_URL}/api/onedrive/notes")
        print(f"   List notes status: {list_response.status_code}")
        
        if list_response.status_code == 200:
            notes_data = list_response.json()
            print(f"   Found {len(notes_data.get('notes', []))} notes in OneDrive")
            
            # Show note previews
            for i, note in enumerate(notes_data.get('notes', [])[:3]):  # First 3 notes
                title = note.get('name', 'Untitled')[:30]
                print(f"     • {title}")
                
        elif list_response.status_code == 401:
            print("   ❌ Unauthorized - session issue")
        else:
            print(f"   ❌ List failed: {list_response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ List notes failed: {e}")
    
    # Step 3: Test pull endpoint directly
    print("\n3️⃣ Testing pull from OneDrive...")
    try:
        # First get CSRF token if needed
        csrf_token = None
        csrf_response = session.get(f"{RAILWAY_URL}/api/csrf-token")
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('csrf_token')
            print(f"   CSRF token: {csrf_token[:10]}..." if csrf_token else "   No CSRF token needed")
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json'
        }
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
        
        # Try pull request
        pull_data = {"merge_strategy": "replace"}
        pull_response = session.post(
            f"{RAILWAY_URL}/api/onedrive/sync/pull", 
            headers=headers,
            json=pull_data
        )
        
        print(f"   Pull status: {pull_response.status_code}")
        
        if pull_response.status_code == 200:
            pull_result = pull_response.json()
            print(f"   Pull success: {pull_result.get('success', False)}")
            print(f"   Notes pulled: {len(pull_result.get('notes', {}))}")
            
            # Show pulled note previews
            notes = pull_result.get('notes', {})
            for note_id, note_data in list(notes.items())[:3]:  # First 3
                text_preview = note_data.get('text', '')[:40]
                print(f"     • {note_id}: {text_preview}...")
                
        else:
            try:
                error_data = pull_response.json()
                print(f"   ❌ Pull failed: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   ❌ Pull failed: {pull_response.text[:100]}")
        
    except Exception as e:
        print(f"   ❌ Pull test failed: {e}")
    
    # Step 4: Check what's actually stored locally
    print("\n4️⃣ Checking local Railway notes...")
    try:
        notes_response = session.get(f"{RAILWAY_URL}/")
        print(f"   Home page status: {notes_response.status_code}")
        
        # Try to access notes API
        api_notes = session.get(f"{RAILWAY_URL}/api/notes")
        print(f"   API notes status: {api_notes.status_code}")
        
        if api_notes.status_code == 200:
            local_notes = api_notes.json()
            print(f"   Local notes count: {len(local_notes.get('notes', {}))}")
        else:
            print(f"   ❌ Can't access local notes: {api_notes.status_code}")
        
    except Exception as e:
        print(f"   ❌ Local notes check failed: {e}")

def test_simple_connectivity():
    """Simple test to verify Railway app is working."""
    print("\n🔗 Simple Connectivity Test")
    print("=" * 40)
    
    try:
        response = requests.get(RAILWAY_URL, timeout=10)
        print(f"Railway URL: {RAILWAY_URL}")
        print(f"Status: {response.status_code}")
        print(f"Title: {response.text[response.text.find('<title>'):response.text.find('</title>') + 8] if '<title>' in response.text else 'No title found'}")
        
    except Exception as e:
        print(f"❌ Connectivity failed: {e}")

def main():
    print("🚀 Railway OneDrive Pull Diagnostic")
    print("=" * 70)
    
    test_simple_connectivity()
    test_railway_onedrive_pull()
    
    print("\n" + "=" * 70)
    print("💡 Troubleshooting Tips:")
    print("  • If authentication fails: Use Railway app to re-authenticate OneDrive")
    print("  • If pull fails: Check desktop app saved notes to OneDrive first")
    print("  • If notes empty: Verify desktop sync button was used to SAVE TO OneDrive")
    print(f"  • Railway URL: {RAILWAY_URL}")

if __name__ == "__main__":
    main()