#!/usr/bin/env python3
"""
Test script to verify the auto-arrangement logic works correctly.
"""

def test_auto_arrangement_logic():
    """Test the auto-arrangement decision logic"""
    
    print("Testing auto-arrangement logic with different window scenarios:")
    print("=" * 60)
    
    # Test scenarios: (width, height, screen_width, screen_height, num_boxes)
    test_cases = [
        (1600, 800, 1920, 1080, 3, "Wide monitor, landscape window"),
        (800, 900, 1920, 1080, 4, "Tall narrow window"),
        (1200, 600, 1920, 1080, 2, "Wide but short window"),
        (600, 800, 1920, 1080, 5, "Many boxes in narrow window"),
        (1500, 1000, 1920, 1080, 3, "Large window, good width"),
        (400, 600, 1920, 1080, 2, "Small compact window"),
        (1920, 800, 1920, 1080, 3, "Full width window"),
        (800, 1080, 1920, 1080, 4, "Full height window"),
    ]
    
    for width, height, screen_w, screen_h, boxes, description in test_cases:
        # Calculate metrics (same logic as in the app)
        aspect_ratio = width / height if height > 0 else 1.0
        width_percentage = (width / screen_w) * 100
        height_percentage = (height / screen_h) * 100
        
        # Apply decision logic
        if aspect_ratio > 1.5:  # Very wide window
            arrangement = "horizontal"
            reason = f"wide window (aspect ratio: {aspect_ratio:.1f})"
        elif height_percentage > 70:  # Using most of screen height
            arrangement = "vertical" 
            reason = f"tall window ({height_percentage:.0f}% of screen height)"
        elif boxes > 3 and aspect_ratio < 1.2:  # Many boxes in narrow window
            arrangement = "vertical"
            reason = f"{boxes} boxes in narrow layout"
        elif width > screen_w * 0.6:  # Wide enough for side-by-side
            arrangement = "horizontal"
            reason = f"sufficient width ({width_percentage:.0f}% of screen)"
        else:  # Default to vertical for smaller windows
            arrangement = "vertical"
            reason = "compact window layout"
        
        print(f"{description}:")
        print(f"  Window: {width}x{height} | Boxes: {boxes}")
        print(f"  Aspect: {aspect_ratio:.1f} | Screen usage: {width_percentage:.0f}%x{height_percentage:.0f}%")
        print(f"  → {arrangement.upper()} ({reason})")
        print()

if __name__ == "__main__":
    test_auto_arrangement_logic()
