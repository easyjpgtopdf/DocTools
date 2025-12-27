"""
Enterprise QA Validator for PDF to Excel Conversion
Ensures production-readiness, deterministic behavior, and auditability
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QAValidationResult:
    """QA validation result with detailed metrics"""
    qa_status: str  # "PASS", "WARN", "FAIL"
    engine_chain: List[str]  # ["docai"] or ["docai", "adobe"]
    confidence_score: float  # 0.0 to 1.0
    billed_pages: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class QAValidator:
    """
    Enterprise QA Validator
    
    Responsibilities:
    1. Validate conversion quality
    2. Check cost and usage limits
    3. Ensure deterministic behavior
    4. Generate audit trail
    """
    
    def __init__(self):
        self.validation_history = []
    
    def validate_conversion(
        self,
        document_name: str,
        layout_source: str,
        pages_processed: int,
        routing_confidence: float,
        unified_layouts: List[Any],
        adobe_guardrails: Optional[Dict] = None,
        user_wants_premium: bool = False
    ) -> QAValidationResult:
        """
        Comprehensive QA validation for a conversion.
        
        Args:
            document_name: Name of the PDF file
            layout_source: "docai" or "adobe"
            pages_processed: Number of pages converted
            routing_confidence: Confidence score (0.0 to 1.0)
            unified_layouts: List of UnifiedLayout objects
            adobe_guardrails: Adobe guardrail metadata (if Adobe was used)
            user_wants_premium: Whether user requested premium mode
        
        Returns:
            QAValidationResult with status, warnings, errors
        """
        logger.info("=" * 80)
        logger.info("QA VALIDATION: Starting enterprise quality check")
        logger.info(f"Document: {document_name}")
        logger.info(f"Engine: {layout_source}")
        logger.info(f"Pages: {pages_processed}")
        logger.info(f"Confidence: {routing_confidence:.2f}")
        logger.info("=" * 80)
        
        result = QAValidationResult(
            qa_status="PASS",  # Default, will be updated if issues found
            engine_chain=[layout_source],
            confidence_score=routing_confidence,
            billed_pages=pages_processed
        )
        
        # ====================================================================
        # CHECK 1: Engine Selection Validation
        # ====================================================================
        engine_warning = self._validate_engine_selection(
            layout_source,
            user_wants_premium,
            routing_confidence,
            adobe_guardrails
        )
        if engine_warning:
            result.warnings.append(engine_warning)
            result.qa_status = "WARN"
        
        # ====================================================================
        # CHECK 2: Layout Quality Validation
        # ====================================================================
        quality_warnings = self._validate_layout_quality(
            unified_layouts,
            layout_source,
            pages_processed
        )
        if quality_warnings:
            result.warnings.extend(quality_warnings)
            if result.qa_status == "PASS":
                result.qa_status = "WARN"
        
        # ====================================================================
        # CHECK 3: Cost Validation
        # ====================================================================
        cost_error = self._validate_cost_limits(
            layout_source,
            pages_processed,
            adobe_guardrails
        )
        if cost_error:
            result.errors.append(cost_error)
            result.qa_status = "FAIL"
        
        # ====================================================================
        # CHECK 4: Determinism Validation
        # ====================================================================
        determinism_check = self._validate_determinism(
            document_name,
            layout_source,
            routing_confidence,
            user_wants_premium
        )
        result.metadata['determinism_hash'] = determinism_check
        
        # ====================================================================
        # CHECK 5: Fallback Safety Validation
        # ====================================================================
        fallback_status = self._validate_fallback_safety(
            layout_source,
            adobe_guardrails
        )
        result.metadata['fallback_safety'] = fallback_status
        
        # ====================================================================
        # FINAL STATUS DETERMINATION
        # ====================================================================
        if result.errors:
            result.qa_status = "FAIL"
        elif result.warnings:
            result.qa_status = "WARN"
        else:
            result.qa_status = "PASS"
        
        # Log final QA result
        logger.info("=" * 80)
        logger.info(f"QA STATUS: {result.qa_status}")
        logger.info(f"Engine Chain: {' → '.join(result.engine_chain)}")
        logger.info(f"Confidence Score: {result.confidence_score:.2f}")
        logger.info(f"Billed Pages: {result.billed_pages}")
        if result.warnings:
            logger.warning(f"Warnings ({len(result.warnings)}): {'; '.join(result.warnings)}")
        if result.errors:
            logger.error(f"Errors ({len(result.errors)}): {'; '.join(result.errors)}")
        logger.info("=" * 80)
        
        # Store validation history
        self.validation_history.append({
            'document': document_name,
            'timestamp': result.timestamp,
            'qa_status': result.qa_status,
            'engine': layout_source,
            'confidence': routing_confidence
        })
        
        return result
    
    def _validate_engine_selection(
        self,
        layout_source: str,
        user_wants_premium: bool,
        routing_confidence: float,
        adobe_guardrails: Optional[Dict]
    ) -> Optional[str]:
        """
        Validate engine selection logic.
        
        Returns:
            Warning message if engine selection is questionable, None otherwise
        """
        # Check: Adobe used without user consent
        if layout_source == "adobe" and not user_wants_premium:
            return "CRITICAL: Adobe used but user did not enable premium toggle"
        
        # Check: Adobe NOT used despite low confidence and user request
        if (layout_source == "docai" and 
            user_wants_premium and 
            routing_confidence < 0.65):
            # This is expected if no structural failures were detected
            if adobe_guardrails:
                gates_failed = adobe_guardrails.get('gates_failed', [])
                if 'no_structural_failures' in gates_failed:
                    return None  # Expected behavior
            return "INFO: User requested premium but DocAI used (no structural failures detected)"
        
        return None
    
    def _validate_layout_quality(
        self,
        unified_layouts: List[Any],
        layout_source: str,
        pages_processed: int
    ) -> List[str]:
        """
        Validate layout quality metrics.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        if not unified_layouts:
            warnings.append("CRITICAL: No layouts generated")
            return warnings
        
        for idx, layout in enumerate(unified_layouts):
            if not hasattr(layout, 'rows') or not layout.rows:
                warnings.append(f"Page {idx + 1}: Empty layout (no rows)")
                continue
            
            # Check for single-column collapse (potential quality issue)
            max_cols = max(len(row) for row in layout.rows) if layout.rows else 0
            if max_cols == 1 and len(layout.rows) > 3:
                warnings.append(f"Page {idx + 1}: Single-column output with {len(layout.rows)} rows (potential collapse)")
            
            # Check for unusually high row count (potential parsing issue)
            if len(layout.rows) > 500:
                warnings.append(f"Page {idx + 1}: Unusually high row count ({len(layout.rows)}) - verify quality")
        
        return warnings
    
    def _validate_cost_limits(
        self,
        layout_source: str,
        pages_processed: int,
        adobe_guardrails: Optional[Dict]
    ) -> Optional[str]:
        """
        Validate cost limits are not exceeded.
        
        Returns:
            Error message if limits exceeded, None otherwise
        """
        # Hard cap: Max 50 pages per Adobe conversion
        if layout_source == "adobe" and pages_processed > 50:
            return f"CRITICAL: Adobe used for {pages_processed} pages (exceeds 50-page limit)"
        
        # Verify estimated cost matches actual pages
        if adobe_guardrails and layout_source == "adobe":
            estimated_pages = adobe_guardrails.get('estimated_adobe_pages', 0)
            if estimated_pages != pages_processed:
                return f"WARNING: Estimated Adobe pages ({estimated_pages}) != actual pages ({pages_processed})"
        
        return None
    
    def _validate_determinism(
        self,
        document_name: str,
        layout_source: str,
        routing_confidence: float,
        user_wants_premium: bool
    ) -> str:
        """
        Generate determinism hash for replay testing.
        
        Returns:
            Hash string for determinism validation
        """
        import hashlib
        
        # Create determinism string
        determinism_str = f"{document_name}|{layout_source}|{routing_confidence:.4f}|{user_wants_premium}"
        determinism_hash = hashlib.md5(determinism_str.encode()).hexdigest()[:16]
        
        logger.info(f"Determinism hash: {determinism_hash} (for replay testing)")
        
        return determinism_hash
    
    def _validate_fallback_safety(
        self,
        layout_source: str,
        adobe_guardrails: Optional[Dict]
    ) -> str:
        """
        Validate fallback safety mechanisms.
        
        Returns:
            Fallback safety status
        """
        if layout_source == "adobe":
            # Adobe was used - verify guardrails were checked
            if not adobe_guardrails:
                return "WARNING: Adobe used without guardrails metadata"
            
            gates_passed = adobe_guardrails.get('gates_passed', [])
            if len(gates_passed) < 5:
                return f"WARNING: Only {len(gates_passed)}/5 gates passed before Adobe"
            
            return "OK: All guardrails passed before Adobe"
        else:
            # DocAI was used - normal operation
            return "OK: DocAI used (no fallback needed)"
    
    def get_daily_adobe_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Get daily Adobe usage for a user (future implementation).
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with daily usage stats
        """
        # TODO: Implement with Redis or database
        return {
            'documents_today': 0,
            'pages_today': 0,
            'credits_today': 0,
            'last_adobe_call': None
        }
    
    def enforce_daily_caps(
        self,
        user_id: str,
        pages_requested: int
    ) -> Tuple[bool, str]:
        """
        Enforce daily Adobe usage caps (future implementation).
        
        Args:
            user_id: User identifier
            pages_requested: Number of pages for this conversion
        
        Returns:
            Tuple of (allowed, reason)
        """
        # TODO: Implement with Redis or database
        MAX_ADOBE_PAGES_PER_DAY = 150
        MAX_ADOBE_DOCS_PER_DAY = 10
        
        usage = self.get_daily_adobe_usage(user_id)
        
        # Check document limit
        if usage['documents_today'] >= MAX_ADOBE_DOCS_PER_DAY:
            return (False, f"Daily limit reached: {MAX_ADOBE_DOCS_PER_DAY} Adobe documents per day")
        
        # Check page limit
        if usage['pages_today'] + pages_requested > MAX_ADOBE_PAGES_PER_DAY:
            return (False, f"Daily page limit exceeded: {MAX_ADOBE_PAGES_PER_DAY} pages per day")
        
        return (True, "Within daily limits")


# Global QA validator instance
_qa_validator_instance = None


def get_qa_validator() -> QAValidator:
    """Get or create global QA validator instance"""
    global _qa_validator_instance
    if _qa_validator_instance is None:
        _qa_validator_instance = QAValidator()
    return _qa_validator_instance

