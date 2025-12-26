"""
Layout Guard for FREE Heuristic Layer.
Ensures safe integration and complete reversibility.

Provides guarded hook point for heuristic processing.
"""

import logging
import os
import shutil
from typing import Optional, Tuple
from pathlib import Path

from . import FREE_HEURISTIC_ENABLED
from .document_type_classifier import classify_document_type, get_classification_rules
from .heuristic_table_fix import fix_table_layout

logger = logging.getLogger(__name__)


def apply_heuristic_layer_if_enabled(excel_path: str) -> Tuple[bool, Optional[str]]:
    """
    Apply heuristic layer to Excel file if enabled and applicable.
    
    This is the SINGLE guarded hook point for heuristic processing.
    Call this AFTER LibreOffice/existing conversion creates the Excel file.
    
    Args:
        excel_path: Path to Excel file (may be modified in-place)
        
    Returns:
        (applied, error_message)
        - applied: True if heuristic was applied, False if skipped/bypassed
        - error_message: Error message if application failed (None if success)
    """
    # Feature flag check - complete bypass if disabled
    if not FREE_HEURISTIC_ENABLED:
        logger.debug("Heuristic layer disabled via feature flag - bypassing")
        return False, None
    
    # Safety check: file must exist
    if not os.path.exists(excel_path):
        logger.warning(f"Excel file not found: {excel_path}")
        return False, "Excel file not found"
    
    try:
        # Step 1: Classify document type
        doc_type = classify_document_type(excel_path)
        logger.info(f"Document type classified as: {doc_type}")
        
        # Step 2: Check if heuristic should be applied for this document type
        classification_rules = get_classification_rules()
        should_apply = classification_rules.get(doc_type, False)
        
        if not should_apply:
            logger.info(f"Heuristic not applied for document type: {doc_type}")
            return False, None
        
        # Step 3: Create backup of original Excel (for reversibility)
        backup_path = excel_path + '.backup'
        try:
            shutil.copy2(excel_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
        except Exception as backup_error:
            logger.warning(f"Could not create backup: {backup_error}")
            # Continue anyway - we'll try to revert if needed
        
        # Step 4: Apply heuristic fixes
        try:
            applied = fix_table_layout(excel_path)
            
            if applied:
                logger.info(f"Heuristic fixes applied successfully for {doc_type}")
                # Keep backup for potential revert
                return True, None
            else:
                logger.info("Heuristic fixes did not modify the file")
                # Remove backup if no changes
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return False, None
                
        except Exception as fix_error:
            logger.error(f"Error applying heuristic fixes: {fix_error}")
            # Revert to backup if available
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, excel_path)
                    os.remove(backup_path)
                    logger.info("Reverted to original Excel file")
                except Exception as revert_error:
                    logger.error(f"Could not revert: {revert_error}")
            return False, f"Heuristic fix failed: {str(fix_error)}"
            
    except Exception as e:
        logger.error(f"Error in heuristic layer: {e}")
        # Ensure we don't break the pipeline - return gracefully
        return False, f"Heuristic layer error: {str(e)}"


def revert_excel_to_backup(excel_path: str) -> bool:
    """
    Revert Excel file to backup (if backup exists).
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        True if reverted, False if backup not found
    """
    backup_path = excel_path + '.backup'
    
    if not os.path.exists(backup_path):
        return False
    
    try:
        shutil.copy2(backup_path, excel_path)
        os.remove(backup_path)
        logger.info(f"Reverted {excel_path} to backup")
        return True
    except Exception as e:
        logger.error(f"Error reverting to backup: {e}")
        return False

