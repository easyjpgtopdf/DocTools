#!/usr/bin/env python3
"""Clean up ppt-to-pdf.html by removing visible JavaScript code and duplicate sections."""

import re

file_path = 'ppt-to-pdf.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the footer placeholder
footer_placeholder = '<div id="global-footer-placeholder"></div>'
footer_idx = content.find(footer_placeholder)

if footer_idx == -1:
    print("Footer placeholder not found!")
    exit(1)

# Find the first script tag after footer (global-components.js)
script_pattern = r'<script src="js/global-components\.js"></script>'
script_match = re.search(script_pattern, content[footer_idx:])

if not script_match:
    print("global-components.js script not found after footer!")
    exit(1)

# Get the position of the script tag
script_start = footer_idx + script_match.start()

# Remove everything between footer placeholder and script tag
# Keep footer placeholder and add a newline, then the script
new_content = content[:footer_idx + len(footer_placeholder)] + '\n\n' + content[script_start:]

# Remove duplicate trust badges sections (keep only the first one)
trust_badges_pattern = r'<div class="trust-badges"[^>]*>.*?</div>\s*</div>'
matches = list(re.finditer(trust_badges_pattern, new_content, re.DOTALL))

# If there are multiple trust badges sections, keep only the first one
if len(matches) > 1:
    # Find the first trust badges section (should be before footer)
    first_trust_idx = new_content.find('<div class="trust-badges"')
    if first_trust_idx != -1:
        # Find where it ends
        first_trust_end = new_content.find('</div>', first_trust_idx) + 6
        first_trust_end = new_content.find('</div>', first_trust_end) + 6
        
        # Remove all other trust badges sections
        for match in matches[1:]:
            if match.start() > first_trust_end:
                new_content = new_content[:match.start()] + new_content[match.end():]
                break

# Remove duplicate footer sections (keep only the one loaded by global-components.js)
footer_pattern = r'<footer>.*?</footer>'
footer_matches = list(re.finditer(footer_pattern, new_content, re.DOTALL))

# If there are multiple footer sections, remove all except the one that should be loaded dynamically
if len(footer_matches) > 0:
    # Keep only the footer placeholder, remove hardcoded footer tags
    for match in footer_matches:
        # Check if this footer is before the global-components script (should be removed)
        if match.start() < new_content.find('<script src="js/global-components.js">'):
            new_content = new_content[:match.start()] + new_content[match.end():]

# Write the cleaned content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Cleaned {file_path} successfully!")

