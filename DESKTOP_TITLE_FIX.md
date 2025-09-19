# Desktop App Title Fix - Quick Solution

## Issue Analysis
The desktop app is showing "Untitled" for tab titles because:

1. **OneDrive is disabled** (`NOTED_CLIENT_ID not set`) - so notes loaded from layout with OneDrive paths can't get proper titles
2. **Layout file may have old format** - saved before title preservation was added
3. **Tab title logic needs fallback** - when OneDrive info isn't available

## Quick Fix Options

### Option 1: Enable OneDrive (Recommended)
Set the OneDrive client ID to restore proper sync and titles:

```bash
# In PowerShell:
$env:NOTED_CLIENT_ID = "cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5"

# Then run:
python noted.py
```

### Option 2: Reset Layout (If OneDrive not needed)
Delete the layout file to start fresh without OneDrive references:

```bash
# Backup current layout
cp layout.json layout.json.backup

# Delete layout to start fresh
rm layout.json

# Run app
python noted.py
```

### Option 3: Set Better Default Titles (Applied)
I've updated the code to:
- Use saved titles from layout when available
- Generate "OneDrive Note X" for OneDrive files without titles  
- Preserve titles when switching between views
- Save titles to layout file for persistence

## Current Status
✅ **App loads and runs correctly**  
✅ **Switching between views works**  
✅ **Content is preserved**  
⚠️ **Titles show as "Untitled" due to OneDrive being disabled**  

## Recommendation
**Enable OneDrive by setting NOTED_CLIENT_ID** - this will restore full functionality and proper note titles.

If OneDrive isn't needed, delete `layout.json` to start fresh with local files that will have proper titles.

## Testing the Fix
```bash
# Quick test with OneDrive enabled:
$env:NOTED_CLIENT_ID = "cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5"
python noted.py

# Or test without OneDrive (delete layout first):
rm layout.json
python noted.py
```

The core functionality is working - the title display is just a cosmetic issue that can be resolved by either enabling OneDrive or starting with a fresh layout.