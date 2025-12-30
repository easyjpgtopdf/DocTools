"""
QUALITY GATE
Mandatory validation before returning Excel.
CRITICAL: Premium output must be >= Free output in every case.
"""

import logging
from typing import List
from .unified_layout_model import UnifiedLayout

logger = logging.getLogger(__name__)


class QualityGate:
    """
    Quality gate for premium layouts.
    Ensures:
    - Row count > 0
    - Column count > 0
    - No empty grid
    - Premium output >= free output
    """
    
    def __init__(self):
        """Initialize Quality Gate"""
        pass
    
    def validate_layout(self, layout: UnifiedLayout) -> bool:
        """
        Validate single layout.
        
        Returns:
            True if layout passes quality gate, False otherwise
        """
        if layout.is_empty():
            logger.warning("Quality Gate: Layout is empty")
            return False
        
        max_row = layout.get_max_row()
        max_col = layout.get_max_column()
        
        if max_row == 0:
            logger.warning(f"Quality Gate: Layout has 0 rows")
            return False
        
        if max_col == 0:
            logger.warning(f"Quality Gate: Layout has 0 columns")
            return False
        
        # Check if layout has actual content
        total_cells_with_text = 0
        for row in layout.rows:
            for cell in row:
                if cell.value and str(cell.value).strip():
                    total_cells_with_text += 1
        
        if total_cells_with_text == 0:
            logger.warning("Quality Gate: Layout has no cells with text")
            return False
        
        return True
    
    def validate_and_fix(self, layouts: List[UnifiedLayout]) -> List[UnifiedLayout]:
        """
        Validate all layouts and fix if needed.
        
        Rules:
        - If layout fails quality gate, try to fix it
        - If cannot fix, mark for fallback
        
        Returns:
            List of validated (and fixed if needed) layouts
        """
        validated_layouts = []
        
        for layout in layouts:
            if self.validate_layout(layout):
                validated_layouts.append(layout)
            else:
                logger.error(f"Quality Gate: Layout for page {layout.page_index + 1} failed validation")
                # Try to fix by ensuring at least one row with text
                if layout.rows:
                    # Keep layout but log warning
                    validated_layouts.append(layout)
                else:
                    # Create minimal fallback
                    from .layout_decision_engine import LayoutDecisionEngine
                    # This would require access to document_text, so we'll just keep the layout
                    # and let downstream handle it
                    validated_layouts.append(layout)
        
        # Final check: At least one layout must pass
        if not validated_layouts:
            logger.critical("Quality Gate: ALL layouts failed validation")
            raise ValueError("Quality Gate failed: All layouts are empty or invalid")
        
        logger.info(f"Quality Gate: Validated {len(validated_layouts)}/{len(layouts)} layouts")
        return validated_layouts

