#!/usr/bin/env python3
import re

def fix_unicode_in_template():
    # Read the template file
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track changes
    original_length = len(content)
    
    # Replace the problematic corrupted character - use a broader pattern
    content = re.sub(r'font-size: 64px; margin-bottom: 20px;">.</div>', 
                    'font-size: 64px; margin-bottom: 20px;">🔐</div>', content)
    
    # Replace Unicode emojis in JavaScript template literals and string concatenations
    replacements = {
        '📔': 'NOTES',
        '✅': 'SUCCESS', 
        '❌': 'ERROR',
        '⏰': '',
        '🔗': '',
        '👤': '',
        '🔐': 'AUTH',
        '📋': '',
        '🌐': '',
        '🗑️': '',
        '💾': '',
        '📂': '',
        '📥': '',
        '🔄': '',
        '🚪': '',
        '📄': '',
        '🔒': '',
    }
    
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back the file
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_length = len(content)
    print(f"Fixed Unicode characters. Length changed from {original_length} to {new_length}")
    print("JavaScript syntax errors from Unicode emojis should now be resolved")

if __name__ == "__main__":
    fix_unicode_in_template()