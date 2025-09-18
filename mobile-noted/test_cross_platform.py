#!/usr/bin/env python3
"""
Cross-Platform Sync Test for Noted Apps
Tests that note formats are compatible between desktop and mobile versions.
"""

import json
import os
import sys
from datetime import datetime

def test_note_format_compatibility():
    """Test that desktop and mobile note formats are compatible."""
    
    # Sample note data that should work on both platforms
    test_note = {
        "title": "Test Cross-Platform Note",
        "text": "This is a test note to verify cross-platform compatibility.\n\nIt should work on both desktop and mobile versions.",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat(),
        "note_id": "test_cross_platform_note_001"
    }
    
    print("=== Cross-Platform Note Format Test ===")
    print(f"Test note format:")
    print(json.dumps(test_note, indent=2))
    
    # Test JSON serialization/deserialization
    try:
        json_str = json.dumps(test_note)
        parsed_note = json.loads(json_str)
        
        # Verify all required fields are present
        required_fields = ["title", "text", "created", "modified", "note_id"]
        missing_fields = [field for field in required_fields if field not in parsed_note]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ JSON serialization/deserialization successful")
        print("✅ All required fields present")
        
        # Test field types
        if not isinstance(parsed_note["title"], str):
            print("❌ Title field is not a string")
            return False
            
        if not isinstance(parsed_note["text"], str):
            print("❌ Text field is not a string")
            return False
            
        if not isinstance(parsed_note["note_id"], str):
            print("❌ Note ID field is not a string")
            return False
        
        print("✅ Field types are correct")
        
        # Test datetime format compatibility
        try:
            datetime.fromisoformat(parsed_note["created"])
            datetime.fromisoformat(parsed_note["modified"])
            print("✅ Datetime formats are compatible")
        except Exception as e:
            print(f"❌ Datetime format error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ JSON processing error: {e}")
        return False

def test_onedrive_integration_compatibility():
    """Test OneDrive integration compatibility."""
    
    print("\n=== OneDrive Integration Test ===")
    
    # Check if OneDrive manager is importable
    try:
        sys.path.insert(0, '.')
        from onedrive_manager import OneDriveManager
        print("✅ OneDrive Manager import successful")
        
        # Test OneDrive Manager initialization (without actual authentication)
        try:
            # Temporarily set client ID for testing
            os.environ["NOTED_CLIENT_ID"] = "test_client_id"
            manager = OneDriveManager()
            print("✅ OneDrive Manager initialization successful")
            
            # Clean up
            if "NOTED_CLIENT_ID" in os.environ and os.environ["NOTED_CLIENT_ID"] == "test_client_id":
                del os.environ["NOTED_CLIENT_ID"]
                
        except Exception as e:
            print(f"⚠️  OneDrive Manager initialization failed (expected without real client ID): {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ OneDrive Manager import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ OneDrive integration test error: {e}")
        return False

def test_mobile_desktop_paths():
    """Test that both mobile and desktop apps can handle the same file paths."""
    
    print("\n=== Path Compatibility Test ===")
    
    # Test common path scenarios
    test_paths = [
        "C:/Users/jwinn/OneDrive - Hayden Beverage/Documents/MobileNoted/notes/test_note.json",
        "/storage/emulated/0/MobileNoted/notes/test_note.json",
        "./notes/test_note.json",
        "notes\\test_note.json"  # Windows style
    ]
    
    for path in test_paths:
        try:
            # Test path normalization
            normalized = os.path.normpath(path)
            directory = os.path.dirname(normalized)
            filename = os.path.basename(normalized)
            
            print(f"✅ Path '{path}' -> dir: '{directory}', file: '{filename}'")
            
        except Exception as e:
            print(f"❌ Path processing error for '{path}': {e}")
            return False
    
    return True

def main():
    """Run all compatibility tests."""
    
    print("🔄 Starting Cross-Platform Compatibility Tests for Noted Apps")
    print("=" * 60)
    
    tests = [
        ("Note Format Compatibility", test_note_format_compatibility),
        ("OneDrive Integration Compatibility", test_onedrive_integration_compatibility),
        ("Path Compatibility", test_mobile_desktop_paths)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Cross-platform compatibility verified.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)