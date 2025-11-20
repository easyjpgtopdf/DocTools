import re
from pathlib import Path

INDEX_PATH = Path('index.html')
HEADER_MATCH = re.search(r'<header>.*?</header>', INDEX_PATH.read_text(encoding='utf-8'), re.S)
if not HEADER_MATCH:
    raise SystemExit('Header not found in index.html')
HEADER_HTML = HEADER_MATCH.group(0)

UPDATED = 0
SKIPPED = 0

for html_path in Path('.').glob('*.html'):
    if html_path.name == 'index.html':
        continue
    text = html_path.read_text(encoding='utf-8')
    new_text, count = re.subn(r'<header>.*?</header>', HEADER_HTML, text, count=1, flags=re.S)
    if count:
        html_path.write_text(new_text, encoding='utf-8')
        UPDATED += 1
    else:
        SKIPPED += 1

print(f'updated={UPDATED} skipped={SKIPPED}')
