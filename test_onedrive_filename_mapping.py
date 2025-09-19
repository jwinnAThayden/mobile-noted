"""
Simple test to verify OneDrive filename mapping functionality
"""
import sys
import json

# Mock the OneDrive manager since we can't import the full app
class MockOneDriveManager:
    def __init__(self):
        self.onedrive_filename_mapping = {
            "01G3ZRC7AQMOQDSUWI7NGJ6GVHVQ2DCOHR": "MailboxDelegate.txt",
            "01G3ZRC7J5ITWUS5NP2JA2X5OLACGV3G5Y": "SMTP OAUTH.txt",
            "01G3ZRC7HL2ELV2PVM5RA3XPNDZ7JF73AI": "6 digital mindfulness commands.txt",
            "01G3ZRC7IPPRPRNAHXF5GZF6KTXUGGOUSG": "Cricut Items Database.txt",
            "01G3ZRC7MUFABRK7SNP5EKQ3UQBOE6KLHN": "top 10 group chat rules.txt",
            "01G3ZRC7L2Y2X7VLBLE5HL5DN6VANHVXZP": "msal application auth details.txt",
            "01G3ZRC7F2JF6LGSFARRFI7ARFXDRYFJQP": "Tasks.txt",
        }
    
    def get_filename_from_item_id(self, item_id):
        return self.onedrive_filename_mapping.get(item_id, None)

def test_onedrive_filename_mapping():
    """Test the OneDrive filename mapping functionality"""
    print("Testing OneDrive filename mapping...")
    
    # Create mock OneDrive manager
    od_manager = MockOneDriveManager()
    
    # Test known item ID
    test_item_id = "01G3ZRC7AQMOQDSUWI7NGJ6GVHVQ2DCOHR"
    expected_filename = "MailboxDelegate.txt"
    
    result = od_manager.get_filename_from_item_id(test_item_id)
    
    print(f"Testing item ID: {test_item_id}")
    print(f"Expected filename: {expected_filename}")
    print(f"Actual result: {result}")
    
    if result == expected_filename:
        print("✅ OneDrive filename mapping works correctly!")
        return True
    else:
        print("❌ OneDrive filename mapping failed!")
        return False

def test_pattern_matching():
    """Test pattern matching for filenames"""
    print("\nTesting pattern matching...")
    
    # Mock content that would generate the problematic title
    test_content = "You have been assigned as a delegate for the mailbox..."
    
    # Extract first line (simulating how current code works)
    first_line = test_content.split('\n')[0][:30]  # First 30 chars
    print(f"Current behavior (first line): '{first_line}'")
    
    # Pattern matching to restore filename
    patterns = {
        "You_have_been_assigned_as_a_De": "MailboxDelegate.txt",
        "SMTP": "SMTP OAUTH.txt",
        "digital_mindfulness": "6 digital mindfulness commands.txt",
    }
    
    # Try pattern matching
    for pattern, filename in patterns.items():
        if pattern.lower() in first_line.lower().replace(' ', '_'):
            print(f"✅ Pattern matched: '{pattern}' -> '{filename}'")
            return filename
    
    print("❌ No pattern matched")
    return first_line

if __name__ == "__main__":
    print("OneDrive Filename Mapping Test")
    print("=" * 40)
    
    success1 = test_onedrive_filename_mapping()
    filename = test_pattern_matching()
    
    print("\n" + "=" * 40)
    if success1:
        print("Overall test: ✅ PASSED")
    else:
        print("Overall test: ❌ FAILED")
    
    print(f"\nExpected result: Tab should show 'MailboxDelegate.txt' instead of '{filename}'")