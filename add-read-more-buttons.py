#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add Read More buttons to blog-articles.html"""

import re

with open("blog-articles.html", "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to find article items and add Read More button
pattern = r'(<div class="article-item"[^>]*>.*?<p style="margin: 0[^"]*?; color: #56607a[^"]*?; font-size: 0\.9rem[^"]*?; line-height: 1\.6;">[^<]+</p>)(\s*</div>)'

def add_read_more(match):
    full_item = match.group(0)
    # Extract href from the h3 link
    href_match = re.search(r'href="([^"]+)"', full_item)
    if href_match:
        href = href_match.group(1)
        # Replace closing p tag to add Read More button
        new_content = full_item.replace(
            '</p>\n                    </div>',
            '</p>\n                        <a href="' + href + '" style="display: inline-flex; align-items: center; gap: 6px; color: #4361ee; text-decoration: none; font-weight: 600; font-size: 0.9rem; transition: all 0.3s; margin-top: 10px;">Read More <i class="fas fa-arrow-right" style="font-size: 0.8rem;"></i></a>\n                    </div>'
        )
        return new_content
    return match.group(0)

# Apply to all article items
content = re.sub(pattern, add_read_more, content, flags=re.DOTALL)

with open("blog-articles.html", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Added Read More buttons to all blog articles")

