#!/usr/bin/env python3
"""
Test script to verify the arrangement functionality works correctly.
This script will create a few text files and verify the arrangement modes work.
"""

import os
import tempfile

# Create test files
test_files = []

# Create a short file
short_content = "This is a short text file.\nJust a few lines.\nNothing major."
short_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
short_file.write(short_content)
short_file.close()
test_files.append(short_file.name)

# Create a medium file
medium_content = """This is a medium-sized text file.
It has more content than the short file.
Multiple paragraphs with various information.
Some technical details and explanations.
More lines to demonstrate content-based arrangement.
Additional content to show weight differences.
Even more text to ensure proper sizing.
Final lines to complete the medium file."""
medium_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
medium_file.write(medium_content)
medium_file.close()
test_files.append(medium_file.name)

# Create a long file
long_content = """This is a long text file with substantial content.
It contains many lines and extensive information.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco.
Laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse.
Cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident.
Sunt in culpa qui officia deserunt mollit anim id est laborum.
Sed ut perspiciatis unde omnis iste natus error sit voluptatem.
Accusantium doloremque laudantium, totam rem aperiam.
Eaque ipsa quae ab illo inventore veritatis et quasi architecto.
Beatae vitae dicta sunt explicabo.
Nemo enim ipsam voluptatem quia voluptas sit aspernatur.
Aut odit aut fugit, sed quia consequuntur magni dolores.
Eos qui ratione voluptatem sequi nesciunt.
Neque porro quisquam est, qui dolorem ipsum quia dolor.
Sit amet, consectetur, adipisci velit, sed quia non numquam.
Eius modi tempora incidunt ut labore et dolore magnam aliquam.
Quaerat voluptatem. Ut enim ad minima veniam.
Quis autem vel eum iure reprehenderit qui in ea voluptate."""
long_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
long_file.write(long_content)
long_file.close()
test_files.append(long_file.name)

print("Test files created:")
for i, file_path in enumerate(test_files, 1):
    with open(file_path, 'r') as f:
        content = f.read()
        line_count = len(content.split('\n'))
        word_count = len(content.split())
    print(f"{i}. {file_path}")
    print(f"   Lines: {line_count}, Words: {word_count}")

print("\nInstructions for testing:")
print("1. Run noted.py")
print("2. Click 'Open Files' and select all three test files")
print("3. Click 'Arrange Boxes' multiple times to cycle through:")
print("   - Intelligent (content-based sizing)")
print("   - Horizontal (equal heights)")
print("   - Vertical (equal heights)")
print("4. Check the status bar for arrangement mode feedback")

print(f"\nTest files are located in: {os.path.dirname(test_files[0])}")
print("Remember to delete them when done testing.")
