"""
FREE Heuristic Layer for PDF to Excel Pipeline.
Lightweight table-fix and document-type classification.

FULLY REVERSIBLE via FREE_HEURISTIC_ENABLED flag.
"""

# Feature flag for complete reversibility
FREE_HEURISTIC_ENABLED = True  # Set to False to completely bypass all heuristic logic

__all__ = [
    'FREE_HEURISTIC_ENABLED',
    'document_type_classifier',
    'heuristic_table_fix',
    'free_layout_guard'
]

