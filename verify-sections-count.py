#!/usr/bin/env python3
"""Quick verification of section counts"""
import re

files = [
    "blog-how-to-use-jpg-to-pdf.html",
    "blog-how-to-use-word-to-pdf.html",
    "blog-how-to-use-excel-to-pdf.html"
]

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            ssl = content.count('<!-- SSL Trust Badges Section -->')
            testimonial = content.count('<!-- Testimonials Section -->')
            related = content.count('class="related-posts"')
            schema = content.count('type="application/ld+json"')
            h1 = len(re.findall(r'<h1[^>]*>', content))
            print(f"{f}:")
            print(f"  SSL Badges: {ssl}")
            print(f"  Testimonials: {testimonial}")
            print(f"  Related Posts: {related}")
            print(f"  Schema: {schema}")
            print(f"  H1 Tags: {h1}")
            print()
    except Exception as e:
        print(f"Error with {f}: {e}")

