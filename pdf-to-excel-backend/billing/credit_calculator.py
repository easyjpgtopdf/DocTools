"""
Centralized Credit Calculator - Per-Page Slab Pricing

Enforces transparent, deterministic pricing based on:
- Engine used (DocAI vs Adobe)
- Page number (slab pricing: 1-5 vs 6+)
- Actual usage (per-page tracking)
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PageBillingInfo:
    """Billing information for a single page"""
    page_number: int
    engine: str  # "docai" or "adobe"
    credits: int
    slab: str  # "1-5" or "6+"


@dataclass
class BillingBreakdown:
    """Complete billing breakdown"""
    total_credits: int
    pages_metadata: List[PageBillingInfo]
    engine_summary: Dict[str, Dict[str, Any]]
    pricing_applied: Dict[str, Dict[str, int]]


class CreditCalculator:
    """
    Centralized credit calculator with per-page slab pricing.
    
    Pricing Rules:
    - DocAI: Pages 1-5 → 5 credits/page, Pages 6+ → 2 credits/page
    - Adobe: Pages 1-5 → 15 credits/page, Pages 6+ → 5 credits/page
    """
    
    # Pricing slabs
    DOCAI_SLAB_1_5 = 5  # credits per page for pages 1-5
    DOCAI_SLAB_6_PLUS = 2  # credits per page for pages 6+
    ADOBE_SLAB_1_5 = 15  # credits per page for pages 1-5
    ADOBE_SLAB_6_PLUS = 5  # credits per page for pages 6+
    
    @staticmethod
    def calculate_credits(pages_metadata: List[Dict[str, Any]]) -> BillingBreakdown:
        """
        Calculate total credits based on per-page engine usage and slab pricing.
        
        Args:
            pages_metadata: List of dicts with 'page' (int) and 'engine' (str) keys
                Example: [{"page": 1, "engine": "docai"}, {"page": 2, "engine": "adobe"}]
        
        Returns:
            BillingBreakdown with total credits, per-page breakdown, and engine summary
        """
        logger.critical("=" * 80)
        logger.critical("CREDIT CALCULATOR: Starting per-page billing calculation")
        logger.critical(f"Input: {len(pages_metadata)} pages")
        logger.critical("=" * 80)
        
        if not pages_metadata:
            logger.warning("No pages metadata provided - returning zero credits")
            return BillingBreakdown(
                total_credits=0,
                pages_metadata=[],
                engine_summary={},
                pricing_applied={}
            )
        
        # Sort pages by page number
        sorted_pages = sorted(pages_metadata, key=lambda x: x.get('page', 0))
        
        # Group pages by engine
        docai_pages = [p for p in sorted_pages if p.get('engine', '').lower() == 'docai']
        adobe_pages = [p for p in sorted_pages if p.get('engine', '').lower() == 'adobe']
        
        logger.critical(f"DocAI pages: {len(docai_pages)}")
        logger.critical(f"Adobe pages: {len(adobe_pages)}")
        
        # Calculate credits per page
        page_billing_info = []
        total_credits = 0
        
        # Process DocAI pages
        for page_info in docai_pages:
            page_num = page_info.get('page', 0)
            if page_num <= 5:
                credits = CreditCalculator.DOCAI_SLAB_1_5
                slab = "1-5"
            else:
                credits = CreditCalculator.DOCAI_SLAB_6_PLUS
                slab = "6+"
            
            page_billing_info.append(PageBillingInfo(
                page_number=page_num,
                engine="docai",
                credits=credits,
                slab=slab
            ))
            total_credits += credits
            
            logger.critical(f"Page {page_num} (DocAI): {credits} credits (slab: {slab})")
        
        # Process Adobe pages
        for page_info in adobe_pages:
            page_num = page_info.get('page', 0)
            if page_num <= 5:
                credits = CreditCalculator.ADOBE_SLAB_1_5
                slab = "1-5"
            else:
                credits = CreditCalculator.ADOBE_SLAB_6_PLUS
                slab = "6+"
            
            page_billing_info.append(PageBillingInfo(
                page_number=page_num,
                engine="adobe",
                credits=credits,
                slab=slab
            ))
            total_credits += credits
            
            logger.critical(f"Page {page_num} (Adobe): {credits} credits (slab: {slab})")
        
        # Build engine summary
        engine_summary = {}
        pricing_applied = {}
        
        if docai_pages:
            docai_slab_1_5_count = len([p for p in docai_pages if p.get('page', 0) <= 5])
            docai_slab_6_plus_count = len([p for p in docai_pages if p.get('page', 0) > 5])
            docai_total = (docai_slab_1_5_count * CreditCalculator.DOCAI_SLAB_1_5 + 
                          docai_slab_6_plus_count * CreditCalculator.DOCAI_SLAB_6_PLUS)
            
            engine_summary['docai'] = {
                'page_count': len(docai_pages),
                'slab_1_5_count': docai_slab_1_5_count,
                'slab_6_plus_count': docai_slab_6_plus_count,
                'total_credits': docai_total
            }
            
            pricing_applied['docai'] = {
                'slab_1_5': CreditCalculator.DOCAI_SLAB_1_5,
                'slab_6_plus': CreditCalculator.DOCAI_SLAB_6_PLUS,
                'slab_1_5_pages': docai_slab_1_5_count,
                'slab_6_plus_pages': docai_slab_6_plus_count
            }
        
        if adobe_pages:
            adobe_slab_1_5_count = len([p for p in adobe_pages if p.get('page', 0) <= 5])
            adobe_slab_6_plus_count = len([p for p in adobe_pages if p.get('page', 0) > 5])
            adobe_total = (adobe_slab_1_5_count * CreditCalculator.ADOBE_SLAB_1_5 + 
                          adobe_slab_6_plus_count * CreditCalculator.ADOBE_SLAB_6_PLUS)
            
            engine_summary['adobe'] = {
                'page_count': len(adobe_pages),
                'slab_1_5_count': adobe_slab_1_5_count,
                'slab_6_plus_count': adobe_slab_6_plus_count,
                'total_credits': adobe_total
            }
            
            pricing_applied['adobe'] = {
                'slab_1_5': CreditCalculator.ADOBE_SLAB_1_5,
                'slab_6_plus': CreditCalculator.ADOBE_SLAB_6_PLUS,
                'slab_1_5_pages': adobe_slab_1_5_count,
                'slab_6_plus_pages': adobe_slab_6_plus_count
            }
        
        # Build billing breakdown
        breakdown = BillingBreakdown(
            total_credits=total_credits,
            pages_metadata=page_billing_info,
            engine_summary=engine_summary,
            pricing_applied=pricing_applied
        )
        
        # Log summary
        logger.critical("=" * 80)
        logger.critical("CREDIT CALCULATOR: Billing Summary")
        if docai_pages:
            docai_summary = engine_summary['docai']
            logger.critical(f"DocAI: {docai_summary['page_count']} pages → "
                          f"{docai_summary['slab_1_5_count']}×{CreditCalculator.DOCAI_SLAB_1_5} + "
                          f"{docai_summary['slab_6_plus_count']}×{CreditCalculator.DOCAI_SLAB_6_PLUS} = "
                          f"{docai_summary['total_credits']} credits")
        if adobe_pages:
            adobe_summary = engine_summary['adobe']
            logger.critical(f"Adobe: {adobe_summary['page_count']} pages → "
                          f"{adobe_summary['slab_1_5_count']}×{CreditCalculator.ADOBE_SLAB_1_5} + "
                          f"{adobe_summary['slab_6_plus_count']}×{CreditCalculator.ADOBE_SLAB_6_PLUS} = "
                          f"{adobe_summary['total_credits']} credits")
        logger.critical(f"TOTAL CREDITS: {total_credits}")
        logger.critical("=" * 80)
        
        return breakdown
    
    @staticmethod
    def format_billing_log(breakdown: BillingBreakdown) -> str:
        """
        Format billing breakdown as human-readable log message.
        
        Example: "Billing: DocAI pages=6 (5*5 + 1*2), Adobe pages=2 (2*15) → Total=39 credits"
        """
        parts = []
        
        if 'docai' in breakdown.engine_summary:
            docai = breakdown.engine_summary['docai']
            if docai['slab_1_5_count'] > 0 and docai['slab_6_plus_count'] > 0:
                parts.append(f"DocAI pages={docai['page_count']} "
                           f"({docai['slab_1_5_count']}×{CreditCalculator.DOCAI_SLAB_1_5} + "
                           f"{docai['slab_6_plus_count']}×{CreditCalculator.DOCAI_SLAB_6_PLUS})")
            elif docai['slab_1_5_count'] > 0:
                parts.append(f"DocAI pages={docai['page_count']} "
                           f"({docai['slab_1_5_count']}×{CreditCalculator.DOCAI_SLAB_1_5})")
            else:
                parts.append(f"DocAI pages={docai['page_count']} "
                           f"({docai['slab_6_plus_count']}×{CreditCalculator.DOCAI_SLAB_6_PLUS})")
        
        if 'adobe' in breakdown.engine_summary:
            adobe = breakdown.engine_summary['adobe']
            if adobe['slab_1_5_count'] > 0 and adobe['slab_6_plus_count'] > 0:
                parts.append(f"Adobe pages={adobe['page_count']} "
                           f"({adobe['slab_1_5_count']}×{CreditCalculator.ADOBE_SLAB_1_5} + "
                           f"{adobe['slab_6_plus_count']}×{CreditCalculator.ADOBE_SLAB_6_PLUS})")
            elif adobe['slab_1_5_count'] > 0:
                parts.append(f"Adobe pages={adobe['page_count']} "
                           f"({adobe['slab_1_5_count']}×{CreditCalculator.ADOBE_SLAB_1_5})")
            else:
                parts.append(f"Adobe pages={adobe['page_count']} "
                           f"({adobe['slab_6_plus_count']}×{CreditCalculator.ADOBE_SLAB_6_PLUS})")
        
        log_msg = f"Billing: {', '.join(parts)} → Total={breakdown.total_credits} credits"
        return log_msg

