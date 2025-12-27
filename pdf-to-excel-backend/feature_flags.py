"""
Enterprise Feature Flags for Production Safety
Allows instant enable/disable of features without redeployment
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Feature flag manager for production safety.
    
    Flags can be controlled via:
    1. Environment variables (highest priority)
    2. Config file (future)
    3. Remote config service (future)
    """
    
    def __init__(self):
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from environment variables"""
        
        # ====================================================================
        # ADOBE PDF EXTRACT FLAGS
        # ====================================================================
        
        # Master kill switch for Adobe
        self.ADOBE_ENABLED = self._get_bool_flag(
            'ADOBE_ENABLED',
            default=True,
            description="Master switch for Adobe PDF Extract API"
        )
        
        # Allow Adobe for premium users
        self.ADOBE_PREMIUM_ONLY = self._get_bool_flag(
            'ADOBE_PREMIUM_ONLY',
            default=True,
            description="Restrict Adobe to premium users only"
        )
        
        # Adobe confidence threshold
        self.ADOBE_CONFIDENCE_THRESHOLD = self._get_float_flag(
            'ADOBE_CONFIDENCE_THRESHOLD',
            default=0.75,
            description="Minimum DocAI confidence to skip Adobe (higher = less Adobe usage)"
        )
        
        # ====================================================================
        # COST CONTROL FLAGS
        # ====================================================================
        
        # Maximum pages per Adobe document
        self.MAX_ADOBE_PAGES_PER_DOC = self._get_int_flag(
            'MAX_ADOBE_PAGES_PER_DOC',
            default=50,
            description="Maximum pages allowed per Adobe conversion"
        )
        
        # Maximum Adobe documents per user per day
        self.MAX_ADOBE_DOCS_PER_DAY = self._get_int_flag(
            'MAX_ADOBE_DOCS_PER_DAY',
            default=10,
            description="Maximum Adobe conversions per user per day"
        )
        
        # Maximum Adobe pages per user per day
        self.MAX_ADOBE_PAGES_PER_DAY = self._get_int_flag(
            'MAX_ADOBE_PAGES_PER_DAY',
            default=150,
            description="Maximum Adobe pages per user per day"
        )
        
        # ====================================================================
        # QUALITY ASSURANCE FLAGS
        # ====================================================================
        
        # Enable QA validation
        self.QA_VALIDATION_ENABLED = self._get_bool_flag(
            'QA_VALIDATION_ENABLED',
            default=True,
            description="Enable comprehensive QA validation"
        )
        
        # Block deployment if QA fails
        self.QA_STRICT_MODE = self._get_bool_flag(
            'QA_STRICT_MODE',
            default=False,
            description="Block conversions if QA validation fails (FAIL status)"
        )
        
        # ====================================================================
        # FALLBACK SAFETY FLAGS
        # ====================================================================
        
        # Auto-fallback to DocAI if Adobe fails
        self.ADOBE_AUTO_FALLBACK = self._get_bool_flag(
            'ADOBE_AUTO_FALLBACK',
            default=True,
            description="Automatically fallback to DocAI if Adobe fails"
        )
        
        # Retry Adobe on failure
        self.ADOBE_RETRY_ON_FAILURE = self._get_bool_flag(
            'ADOBE_RETRY_ON_FAILURE',
            default=False,
            description="Retry Adobe API call on failure (increases cost risk)"
        )
        
        # ====================================================================
        # LOGGING FLAGS
        # ====================================================================
        
        # Detailed cost logging
        self.DETAILED_COST_LOGGING = self._get_bool_flag(
            'DETAILED_COST_LOGGING',
            default=True,
            description="Log detailed cost breakdown per conversion"
        )
        
        # Audit trail logging
        self.AUDIT_TRAIL_ENABLED = self._get_bool_flag(
            'AUDIT_TRAIL_ENABLED',
            default=True,
            description="Enable comprehensive audit trail logging"
        )
        
        # Log all flag values at startup
        self._log_flags()
    
    def _get_bool_flag(self, name: str, default: bool, description: str) -> bool:
        """Get boolean flag from environment"""
        value = os.environ.get(name, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int_flag(self, name: str, default: int, description: str) -> int:
        """Get integer flag from environment"""
        try:
            return int(os.environ.get(name, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer for {name}, using default: {default}")
            return default
    
    def _get_float_flag(self, name: str, default: float, description: str) -> float:
        """Get float flag from environment"""
        try:
            return float(os.environ.get(name, str(default)))
        except ValueError:
            logger.warning(f"Invalid float for {name}, using default: {default}")
            return default
    
    def _log_flags(self):
        """Log all feature flags at startup"""
        logger.info("=" * 80)
        logger.info("FEATURE FLAGS CONFIGURATION")
        logger.info("=" * 80)
        logger.info("Adobe PDF Extract:")
        logger.info(f"  ADOBE_ENABLED: {self.ADOBE_ENABLED}")
        logger.info(f"  ADOBE_PREMIUM_ONLY: {self.ADOBE_PREMIUM_ONLY}")
        logger.info(f"  ADOBE_CONFIDENCE_THRESHOLD: {self.ADOBE_CONFIDENCE_THRESHOLD}")
        logger.info("Cost Control:")
        logger.info(f"  MAX_ADOBE_PAGES_PER_DOC: {self.MAX_ADOBE_PAGES_PER_DOC}")
        logger.info(f"  MAX_ADOBE_DOCS_PER_DAY: {self.MAX_ADOBE_DOCS_PER_DAY}")
        logger.info(f"  MAX_ADOBE_PAGES_PER_DAY: {self.MAX_ADOBE_PAGES_PER_DAY}")
        logger.info("Quality Assurance:")
        logger.info(f"  QA_VALIDATION_ENABLED: {self.QA_VALIDATION_ENABLED}")
        logger.info(f"  QA_STRICT_MODE: {self.QA_STRICT_MODE}")
        logger.info("Fallback Safety:")
        logger.info(f"  ADOBE_AUTO_FALLBACK: {self.ADOBE_AUTO_FALLBACK}")
        logger.info(f"  ADOBE_RETRY_ON_FAILURE: {self.ADOBE_RETRY_ON_FAILURE}")
        logger.info("Logging:")
        logger.info(f"  DETAILED_COST_LOGGING: {self.DETAILED_COST_LOGGING}")
        logger.info(f"  AUDIT_TRAIL_ENABLED: {self.AUDIT_TRAIL_ENABLED}")
        logger.info("=" * 80)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export flags as dictionary"""
        return {
            'adobe_enabled': self.ADOBE_ENABLED,
            'adobe_premium_only': self.ADOBE_PREMIUM_ONLY,
            'adobe_confidence_threshold': self.ADOBE_CONFIDENCE_THRESHOLD,
            'max_adobe_pages_per_doc': self.MAX_ADOBE_PAGES_PER_DOC,
            'max_adobe_docs_per_day': self.MAX_ADOBE_DOCS_PER_DAY,
            'max_adobe_pages_per_day': self.MAX_ADOBE_PAGES_PER_DAY,
            'qa_validation_enabled': self.QA_VALIDATION_ENABLED,
            'qa_strict_mode': self.QA_STRICT_MODE,
            'adobe_auto_fallback': self.ADOBE_AUTO_FALLBACK,
            'adobe_retry_on_failure': self.ADOBE_RETRY_ON_FAILURE,
            'detailed_cost_logging': self.DETAILED_COST_LOGGING,
            'audit_trail_enabled': self.AUDIT_TRAIL_ENABLED
        }
    
    def can_use_adobe(
        self,
        user_wants_premium: bool,
        docai_confidence: float,
        page_count: int
    ) -> Tuple[bool, str]:
        """
        Check if Adobe can be used based on feature flags.
        
        Args:
            user_wants_premium: User enabled premium toggle
            docai_confidence: DocAI routing confidence
            page_count: Number of pages in document
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check master kill switch
        if not self.ADOBE_ENABLED:
            return (False, "Adobe PDF Extract is disabled (feature flag)")
        
        # Check premium-only restriction
        if self.ADOBE_PREMIUM_ONLY and not user_wants_premium:
            return (False, "Adobe requires premium toggle enabled")
        
        # Check confidence threshold
        if docai_confidence >= self.ADOBE_CONFIDENCE_THRESHOLD:
            return (False, f"DocAI confidence {docai_confidence:.2f} >= threshold {self.ADOBE_CONFIDENCE_THRESHOLD}")
        
        # Check page limit
        if page_count > self.MAX_ADOBE_PAGES_PER_DOC:
            return (False, f"Document has {page_count} pages (exceeds limit of {self.MAX_ADOBE_PAGES_PER_DOC})")
        
        return (True, "Adobe allowed by feature flags")


# Global feature flags instance
_feature_flags_instance = None


def get_feature_flags() -> FeatureFlags:
    """Get or create global feature flags instance"""
    global _feature_flags_instance
    if _feature_flags_instance is None:
        _feature_flags_instance = FeatureFlags()
    return _feature_flags_instance


# Convenience function for instant Adobe disable
def disable_adobe_immediately():
    """
    Emergency function to disable Adobe PDF Extract instantly.
    Can be called from admin API or monitoring alerts.
    """
    flags = get_feature_flags()
    flags.ADOBE_ENABLED = False
    logger.critical("🚨 ADOBE PDF EXTRACT DISABLED IMMEDIATELY via emergency function")
    return "Adobe PDF Extract disabled"


def enable_adobe():
    """Re-enable Adobe PDF Extract"""
    flags = get_feature_flags()
    flags.ADOBE_ENABLED = True
    logger.info("✅ Adobe PDF Extract re-enabled")
    return "Adobe PDF Extract enabled"

