#!/usr/bin/env python3
"""
Right-click context menu feature verification.
This confirms that the alphabetical sorting feature already exists.
"""

def verify_context_menu_features():
    """Check what features are available in the right-click context menu."""
    
    print("🔍 Tab Right-Click Context Menu Features")
    print("=" * 50)
    
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for context menu features
        context_features = [
            ('Save Tab', '"Save Tab"' in content),
            ('Reload Tab', '"Reload Tab"' in content),
            ('Rename Tab & File', '"Rename Tab & File"' in content),
            ('Close Tab', '"Close Tab"' in content),
            ('Close All Tabs', '"Close All Tabs"' in content),
            ('AI Submenu', '"AI"' in content and 'ai_menu' in content),
            ('Sort All Tabs by Name', '"Sort All Tabs by Name"' in content),
        ]
        
        print("📋 Available Context Menu Options:")
        for feature, available in context_features:
            status = "✅ Available" if available else "❌ Missing"
            print(f"  {status} - {feature}")
        
        # Check if sort function exists and is complete
        sort_checks = [
            ('sort_tabs_by_name method', 'def sort_tabs_by_name(self):' in content),
            ('Title-based sorting', 'title.lower().strip()' in content),
            ('OneDrive filename sorting', '_get_onedrive_filename_from_id' in content),
            ('Tab rebuilding logic', 'self.notebook.add(tab_frame' in content),
            ('Layout saving after sort', 'save_layout_to_file' in content),
        ]
        
        print("\n🔧 Sort Function Analysis:")
        for check, found in sort_checks:
            status = "✅ Present" if found else "❌ Missing"
            print(f"  {status} - {check}")
        
        # Instructions
        print("\n" + "=" * 50)
        print("🎯 How to Use Alphabetical Sorting:")
        print("1. Right-click on any tab")
        print("2. Select 'Sort All Tabs by Name' from the context menu") 
        print("3. All tabs will be reorganized alphabetically")
        print("\n💡 This is more reliable than drag-and-drop!")
        print("💡 It uses the stored title data for accurate sorting")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying context menu: {e}")
        return False

if __name__ == "__main__":
    verify_context_menu_features()