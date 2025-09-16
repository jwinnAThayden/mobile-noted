#!/bin/bash

# Script to patch pyjnius long type error for Python 3 compatibility
# Run this in your Linux VM at the project root: /home/jwinn/Documents/noted/mobile-noted

echo "=== Pyjnius Python 3 Compatibility Patcher ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"

# Step 1: Find all jnius_utils.pxi files
echo -e "\n=== Finding all jnius_utils.pxi files ==="
find . -name "jnius_utils.pxi" -type f 2>/dev/null | while read -r file; do
    echo "Found: $file"
done

# Step 2: Find files with the problematic long usage
echo -e "\n=== Searching for isinstance(arg, long) usage ==="
grep -r --include="*.pxi" -n "isinstance(arg, long)" . 2>/dev/null | head -20

# Step 3: Patch all occurrences
echo -e "\n=== Patching files ==="
find . -name "jnius_utils.pxi" -type f 2>/dev/null | while read -r file; do
    if [ -f "$file" ]; then
        echo "Processing: $file"
        
        # Check if already patched
        if grep -q "long = int" "$file"; then
            echo "  Already has long = int alias"
        else
            echo "  Adding long = int alias at top"
            sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$file"
        fi
        
        # Replace isinstance(arg, long) with isinstance(arg, int)
        if grep -q "isinstance(arg, long)" "$file"; then
            echo "  Replacing isinstance(arg, long) with isinstance(arg, int)"
            sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$file"
        else
            echo "  No isinstance(arg, long) found"
        fi
        
        echo "  First 10 lines after patching:"
        head -n 10 "$file" | sed 's/^/    /'
    fi
done

# Step 4: Also patch the python-for-android recipe source
echo -e "\n=== Patching recipe source ==="
RECIPE_FILE=".buildozer/android/platform/python-for-android/pythonforandroid/recipes/pyjnius/jnius_utils.pxi"
if [ -f "$RECIPE_FILE" ]; then
    echo "Found recipe file: $RECIPE_FILE"
    if ! grep -q "long = int" "$RECIPE_FILE"; then
        sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$RECIPE_FILE"
        echo "  Added long = int alias"
    fi
    sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$RECIPE_FILE"
    echo "  Replaced isinstance(arg, long)"
else
    echo "Recipe file not found: $RECIPE_FILE"
fi

# Step 5: Remove build caches
echo -e "\n=== Cleaning build caches ==="
rm -rf .buildozer/android/platform/build-*/other_builds/pyjnius* 2>/dev/null && echo "Removed pyjnius build caches" || echo "No pyjnius caches to remove"

# Step 6: Verify no remaining issues
echo -e "\n=== Verification ==="
remaining=$(grep -r --include="*.pxi" -c "isinstance(arg, long)" . 2>/dev/null | grep -v ":0" || true)
if [ -z "$remaining" ]; then
    echo "✓ No remaining isinstance(arg, long) found"
else
    echo "⚠ Still found isinstance(arg, long) in:"
    echo "$remaining"
fi

echo -e "\n=== Script complete ==="
echo "Now run: buildozer -v android debug"
