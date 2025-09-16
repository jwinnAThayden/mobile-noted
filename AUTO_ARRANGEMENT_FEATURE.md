# Auto-Arrangement Feature Documentation

## Overview
The "Auto Arrange" button now intelligently chooses between horizontal and vertical box arrangements based on the current window dimensions, aspect ratio, and content context.

## How It Works

### Automatic Decision Logic
The system analyzes several factors to determine the optimal arrangement:

1. **Aspect Ratio Analysis**
   - Windows with aspect ratio > 1.5 prefer horizontal (side-by-side) arrangement
   - Narrow windows favor vertical (stacked) arrangement

2. **Screen Usage Analysis**
   - Windows using >70% of screen height → vertical arrangement
   - Windows using >60% of screen width → horizontal arrangement

3. **Content Context**
   - Many boxes (>3) in narrow windows → vertical arrangement
   - Few boxes in wide windows → horizontal arrangement

4. **Fallback Logic**
   - Small or compact windows → vertical arrangement (default)

### Arrangement Modes

#### Horizontal Mode ("side-by-side")
- All text boxes receive uniform height
- Optimized for comparing content across boxes
- Triggered by: wide windows, landscape orientations, sufficient width

#### Vertical Mode ("stacked")
- Equal height distribution among all boxes
- Optimized for sequential reading and editing
- Triggered by: tall windows, many boxes, narrow layouts

## Features

### Manual Trigger
- Click "Auto Arrange" button to manually trigger smart arrangement
- System analyzes current window state and applies optimal layout
- Status bar shows the chosen arrangement and reasoning

### Automatic Trigger
- Window resize events automatically trigger re-arrangement
- Debounced to prevent excessive re-arrangements during dragging
- Only triggers for significant size changes (>50 pixels)
- 500ms delay after resize stops before re-arranging

### User Feedback
- Status bar displays arrangement choice and reasoning
- Examples:
  - "Auto-arranged: side-by-side (wide window, aspect ratio: 2.0)"
  - "Auto-arranged: stacked (tall window, 83% of screen height)"
  - "Auto-arranged: vertical (5 boxes in narrow layout)"

## Example Scenarios

### Wide Monitor Usage
- **Window:** 1600x800 on 1920x1080 screen
- **Result:** Horizontal arrangement (side-by-side)
- **Reason:** Wide window with 2.0 aspect ratio

### Tall Narrow Window
- **Window:** 800x900 on 1920x1080 screen  
- **Result:** Vertical arrangement (stacked)
- **Reason:** Tall window using 83% of screen height

### Many Boxes
- **Window:** 600x800 with 5 text boxes
- **Result:** Vertical arrangement (stacked)
- **Reason:** Many boxes in narrow layout

### Full Screen
- **Window:** 1920x800 on 1920x1080 screen
- **Result:** Horizontal arrangement (side-by-side)
- **Reason:** Full width with high aspect ratio

## Technical Implementation

### Core Methods
- `cycle_box_arrangement()` - Main auto-arrangement logic
- `_arrange_horizontal()` - Implements horizontal layout
- `_arrange_vertical()` - Implements vertical layout
- `_on_window_configure()` - Handles resize events
- `_auto_arrange_after_resize()` - Debounced auto-arrangement

### Configuration
- Resize sensitivity: 50 pixels minimum change
- Resize debounce: 500ms delay
- Status feedback duration: 3 seconds
- Aspect ratio threshold: 1.5 for wide windows
- Height usage threshold: 70% for tall windows
- Width usage threshold: 60% for wide enough

## Benefits

1. **Adaptive Interface**: Layout automatically optimizes for current usage
2. **Improved Productivity**: Always optimal arrangement without manual intervention
3. **Context Awareness**: Considers both window dimensions and content volume
4. **Seamless Experience**: Automatic re-arrangement on window resize
5. **User Control**: Manual trigger available when needed

## Usage Tips

1. **Resize Window**: Simply resize the application window to trigger auto-arrangement
2. **Manual Override**: Click "Auto Arrange" anytime to re-evaluate layout
3. **Monitor Status**: Watch status bar for arrangement reasoning
4. **Multiple Monitors**: Works with different screen sizes and resolutions
5. **Content Planning**: Add more boxes to influence arrangement decisions

The auto-arrangement feature transforms the static layout system into a dynamic, intelligent interface that adapts to your workflow and screen usage patterns.
