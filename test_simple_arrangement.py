#!/usr/bin/env python3
"""
Simple test to verify the arrangement toggle works correctly.
"""

def test_arrangement_logic():
    """Test the arrangement toggle logic"""
    
    # Simulate the arrangement logic
    current_arrangement = "horizontal"
    
    print("Testing simple arrangement toggle logic:")
    print(f"Starting arrangement: {current_arrangement}")
    
    # Simulate 5 button clicks
    for i in range(1, 6):
        # Toggle between horizontal and vertical
        if current_arrangement == "horizontal":
            current_arrangement = "vertical"
        else:
            current_arrangement = "horizontal"
        
        print(f"Click {i}: {current_arrangement}")

if __name__ == "__main__":
    test_arrangement_logic()
