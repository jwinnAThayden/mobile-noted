"""
Complete Cross-Platform Sync Test
Test desktop save → OneDrive → Railway pull workflow
"""

import subprocess
import time
import requests
import json
from datetime import datetime

RAILWAY_URL = "https://mobile-noted-production.up.railway.app"

def test_desktop_onedrive_save():
    """Instruct user to test desktop save functionality."""
    print("🖥️ Desktop OneDrive Save Test")
    print("=" * 50)
    
    print("Please follow these steps in your desktop app:")
    print("")
    print("1️⃣ Make sure NOTED_CLIENT_ID environment variable is set")
    print("   (Already set in current PowerShell session)")
    print("")
    print("2️⃣ Open the desktop Noted app:")
    print("   python noted.py")
    print("")
    print("3️⃣ Create a few test notes with some content")
    print("")
    print("4️⃣ Click the 'OneDrive Sync' button")
    print("")
    print("5️⃣ Complete the device authentication")
    print("")
    print("6️⃣ When prompted, choose 'YES' to save TO OneDrive")
    print("   (This is the key fix - previously it only loaded FROM OneDrive)")
    print("")
    print("7️⃣ Verify you see a success message")
    print("")
    
    input("Press Enter when you've completed the desktop sync...")
    return True

def test_railway_pull_after_desktop_save():
    """Test Railway pull after desktop save."""
    print("\n📱 Railway Pull Test (After Desktop Save)")
    print("=" * 60)
    
    session = requests.Session()
    
    # Check OneDrive notes count
    print("1️⃣ Checking OneDrive for notes...")
    try:
        auth_response = session.get(f"{RAILWAY_URL}/api/onedrive/auth/simple-check")
        if not auth_response.json().get('authenticated'):
            print("   ❌ Railway not authenticated with OneDrive")
            return False
            
        list_response = session.get(f"{RAILWAY_URL}/api/onedrive/notes")
        if list_response.status_code == 200:
            notes_data = list_response.json()
            notes_count = len(notes_data.get('notes', []))
            print(f"   📋 Found {notes_count} notes in OneDrive")
            
            if notes_count == 0:
                print("   ❌ No notes found - desktop save may have failed")
                return False
            else:
                print("   ✅ Notes found in OneDrive!")
                
                # Show note previews
                for note in notes_data.get('notes', [])[:3]:
                    name = note.get('name', 'Untitled')
                    modified = note.get('modified', 'Unknown')
                    print(f"     • {name} (modified: {modified})")
        else:
            print(f"   ❌ Failed to list notes: {list_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking OneDrive: {e}")
        return False
    
    # Test pull
    print("\n2️⃣ Pulling notes to Railway app...")
    try:
        # Get CSRF token
        csrf_response = session.get(f"{RAILWAY_URL}/api/csrf-token")
        csrf_token = csrf_response.json().get('csrf_token') if csrf_response.status_code == 200 else None
        
        headers = {'Content-Type': 'application/json'}
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
            
        pull_response = session.post(
            f"{RAILWAY_URL}/api/onedrive/sync/pull",
            headers=headers,
            json={"merge_strategy": "replace"}
        )
        
        if pull_response.status_code == 200:
            pull_data = pull_response.json()
            pulled_count = len(pull_data.get('notes', {}))
            print(f"   📥 Pulled {pulled_count} notes successfully!")
            
            if pulled_count > 0:
                print("   ✅ Cross-platform sync working!")
                
                # Show pulled note previews
                notes = pull_data.get('notes', {})
                for note_id, note_data in list(notes.items())[:3]:
                    text_preview = note_data.get('text', '')[:50]
                    created = note_data.get('created', 'Unknown')
                    print(f"     • {note_id}: \"{text_preview}...\" (created: {created})")
                    
                return True
            else:
                print("   ❌ No notes were pulled")
                return False
        else:
            error_data = pull_response.json() if pull_response.headers.get('content-type', '').startswith('application/json') else {'error': pull_response.text[:100]}
            print(f"   ❌ Pull failed: {error_data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Pull error: {e}")
        return False

def verify_railway_notes():
    """Verify notes are now visible in Railway app."""
    print("\n3️⃣ Verifying notes in Railway app...")
    
    session = requests.Session()
    
    try:
        api_response = session.get(f"{RAILWAY_URL}/api/notes")
        if api_response.status_code == 200:
            local_notes = api_response.json()
            notes_count = len(local_notes.get('notes', {}))
            print(f"   📱 Railway app now has {notes_count} notes locally")
            
            if notes_count > 0:
                print("   ✅ Notes successfully synced to Railway!")
                print(f"   🌐 View them at: {RAILWAY_URL}")
                return True
            else:
                print("   ❌ No local notes in Railway app")
                return False
        else:
            print(f"   ❌ Can't check local notes: {api_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

def main():
    print("🔄 Complete Cross-Platform Sync Test")
    print("=" * 70)
    print(f"Desktop → OneDrive → Railway ({RAILWAY_URL})")
    print("=" * 70)
    
    # Step 1: Desktop save
    if not test_desktop_onedrive_save():
        print("\n❌ Desktop save step failed")
        return
    
    # Step 2: Railway pull
    if not test_railway_pull_after_desktop_save():
        print("\n❌ Railway pull step failed")
        return
    
    # Step 3: Verify Railway
    if not verify_railway_notes():
        print("\n❌ Railway verification failed")
        return
    
    # Success!
    print("\n" + "🎉" * 20)
    print("✅ CROSS-PLATFORM SYNC WORKING!")
    print("🎉" * 20)
    print("")
    print("✨ Your notes are now synchronized between:")
    print("   🖥️  Desktop Noted app")
    print("   ☁️  OneDrive cloud storage")
    print(f"   📱 Railway web app: {RAILWAY_URL}")
    print("")
    print("🚀 Next steps:")
    print("   • Use desktop app to create/edit notes")
    print("   • Click 'OneDrive Sync' → 'YES' to save to cloud")
    print("   • Use Railway app 'Pull from OneDrive' to sync")
    print("   • Enjoy cross-platform note access!")

if __name__ == "__main__":
    main()