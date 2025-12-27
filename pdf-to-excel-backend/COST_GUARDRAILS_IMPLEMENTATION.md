# Cost Guardrails & Confidence Thresholds Implementation

## 📋 Overview
This document details the implementation of **STEP 4: CONFIDENCE THRESHOLDS & COST GUARDRAILS** to ensure Adobe PDF Extract is used ONLY when structurally necessary, with strict cost control and deterministic behavior.

---

## 🎯 Goals Achieved
✅ Adobe fallback used ONLY when necessary  
✅ Strict cost control with multiple gates  
✅ Deterministic behavior (same document → same decision)  
✅ Transparent user control via premium toggle  
✅ Comprehensive logging for cost tracking  

---

## 🚪 5-Gate System

### Gate 1: Premium Toggle (User Control)
**Rule**: Adobe fallback is disabled unless user explicitly enables premium mode.

```python
if not user_wants_premium:
    return (False, "User did not enable premium mode - Adobe skipped", metadata)
```

**Purpose**: No hidden charges. Users have full control.

---

### Gate 2: Confidence Threshold
**Rule**: If Document AI confidence ≥ 0.75, Adobe is not needed.

```python
if docai_confidence >= 0.75:
    return (False, f"Document AI confidence {docai_confidence:.2f} >= 0.75 - Adobe not needed", metadata)
```

**Purpose**: Use Adobe only for low-confidence cases.

---

### Gate 3: Structural Failure Detection
**Rule**: Adobe is allowed ONLY if at least one structural failure exists.

**Failure Checks**:
1. **Single-column collapse**: `detected_rows >= 3 AND detected_columns == 1`
2. **Insufficient columns**: `detected_columns < 2`
3. **Complex merges**: `merged_cell_count >= 3`
4. **High visual complexity**: `blocks > 100 + varied_font_sizes >= 4`
5. **Complex document type**: `bank_statement`, `govt_form`, `utility_bill`

```python
has_failures, failure_reasons = self.check_structural_failures(full_structure, unified_layouts)
if not has_failures:
    return (False, "No structural failures detected - Adobe not needed", metadata)
```

**Purpose**: Prevent unnecessary Adobe calls for well-structured documents.

---

### Gate 4: Page Count Guard
**Rule**: If `page_count > 20`, warn user (would require confirmation in production).

```python
if page_count > 20:
    logger.warning(f"⚠️ GATE 4 WARNING: {page_count} pages exceed threshold - would require confirmation")
```

**Purpose**: Prevent unexpected high costs for large documents.

---

### Gate 5: Cost Caps
**Rules**:
- Max Adobe pages per document: **50**
- Max Adobe calls per document: **3** (future)

```python
MAX_ADOBE_PAGES_PER_DOC = 50
if page_count > MAX_ADOBE_PAGES_PER_DOC:
    return (False, f"Document has {page_count} pages, exceeds Adobe limit of {MAX_ADOBE_PAGES_PER_DOC}", metadata)
```

**Purpose**: Hard cost limits to prevent runaway expenses.

---

## 💰 Credit Model Implementation

### Standard (DocAI) Pricing
- **1-10 pages**: 5 credits/page
- **11+ pages**: 2 credits/page (for pages 11+)

### Premium (Adobe) Pricing
- **1-10 pages**: 15 credits/page
- **11+ pages**: 5 credits/page (for pages 11+)

### Implementation

```python
def calculate_credits_based_on_engine(pages: int, engine_source: str) -> Tuple[int, float]:
    if engine_source == 'adobe':
        # Premium pricing
        if pages <= 10:
            return (pages * 15, 15.0)
        else:
            total = (10 * 15) + ((pages - 10) * 5)
            avg = total / pages
            return (total, avg)
    else:
        # Standard pricing
        if pages <= 10:
            return (pages * 5, 5.0)
        else:
            total = (10 * 5) + ((pages - 10) * 2)
            avg = total / pages
            return (total, avg)
```

**Example**:
- 5-page document (DocAI): 5 × 5 = **25 credits**
- 5-page document (Adobe): 5 × 15 = **75 credits**
- 15-page document (DocAI): (10 × 5) + (5 × 2) = **60 credits**
- 15-page document (Adobe): (10 × 15) + (5 × 5) = **175 credits**

---

## 📊 Logging (MANDATORY)

All Adobe fallback decisions are logged with:

```
ADOBE FALLBACK GUARDRAILS CHECK
Adobe fallback allowed: YES/NO
Reason: <detailed reason>
Gates passed: premium_toggle_on, low_confidence, structural_failures, page_count_ok, within_cost_caps
Gates failed: <any failed gates>
Estimated Adobe cost: X credits for Y pages
```

If Adobe is used:
```
🚀 ADOBE FALLBACK: Starting extraction
Structural failures: Single-column collapse: 8 rows but only 1 column
Document: sample.pdf (5 pages)
✅ Adobe SUCCESS: Replacing 1 DocAI layouts with 1 Adobe layouts
Rows: 8, Columns: 5
Merged cells: 2
```

Credit calculation:
```
CREDIT CALCULATION
Pages processed: 5
Engine used: adobe
Average cost: 15.00 credits/page
Total cost: 75 credits
```

---

## 🔄 Complete Flow

### User Workflow
1. User uploads PDF
2. User enables "High Accuracy Mode (Premium)" toggle (optional)
3. Backend checks 5 gates
4. If all gates pass → Adobe is used
5. User is charged actual credits (DocAI or Adobe pricing)
6. Result shows engine used, accuracy, credits deducted

### Backend Decision Flow
```
User uploads PDF
    ↓
Premium toggle enabled? → NO → Use DocAI only
    ↓ YES
DocAI confidence < 0.75? → NO → Use DocAI only
    ↓ YES
Structural failures exist? → NO → Use DocAI only
    ↓ YES
Page count <= 20? → NO → Warn user (continue in production after confirmation)
    ↓ YES
Page count <= 50? → NO → Use DocAI only
    ↓ YES
✅ ALL GATES PASSED → Use Adobe PDF Extract
```

---

## 🔧 Files Modified

### 1. `premium_layout/decision_router.py`
**Added**:
- `check_structural_failures()`: Detects 5 types of structural issues
- `should_enable_adobe_with_guardrails()`: Implements 5-gate system
- Comprehensive logging

### 2. `docai_service.py`
**Modified**:
- Added `user_wants_premium` parameter to `process_pdf_to_excel_docai()`
- Replaced old `should_enable_adobe_fallback()` with new `should_enable_adobe_with_guardrails()`
- Enhanced logging with guardrail metadata

### 3. `main.py`
**Modified**:
- Extract `user_wants_premium` from form data
- Pass `user_wants_premium` to `process_pdf_to_excel_docai()`
- Implement `calculate_credits_based_on_engine()` function
- Calculate credits based on ACTUAL engine used (DocAI vs Adobe)
- Add guardrail metadata to response

---

## 🧪 Testing Scenarios

### Scenario 1: User Disables Premium Toggle
**Expected**: Adobe never called, DocAI used, standard pricing applied
**Log**: `"Adobe fallback NOT triggered: User did not enable premium mode"`

### Scenario 2: High Confidence Document
**Expected**: Adobe not called even if toggle is ON
**Log**: `"Adobe fallback NOT triggered: Document AI confidence 0.85 >= 0.75"`

### Scenario 3: Well-Structured Document
**Expected**: Adobe not called (no structural failures)
**Log**: `"Adobe fallback NOT triggered: No structural failures detected"`

### Scenario 4: Complex Document (All Gates Pass)
**Expected**: Adobe called, premium pricing applied
**Log**: 
```
✅ GATE 1 PASSED: User enabled premium toggle
✅ GATE 2 PASSED: Low confidence (0.55 < 0.75)
✅ GATE 3 PASSED: Structural failures detected: Single-column collapse: 8 rows but only 1 column
✅ GATE 4 PASSED: Page count within limits
✅ GATE 5 PASSED: Within cost caps
🚀 ALL ADOBE GUARDRAILS PASSED
```

### Scenario 5: Large Document (51 pages)
**Expected**: Adobe not called (exceeds 50-page limit)
**Log**: `"Adobe fallback NOT triggered: Document has 51 pages, exceeds Adobe limit of 50"`

---

## 📈 Cost Tracking Metadata

Response includes:
```json
{
  "status": "success",
  "layout_source": "adobe",
  "creditsDeducted": 75,
  "pricing": {
    "type": "per_page",
    "cost_per_page": 15.0,
    "total_cost": 75,
    "pages": 5,
    "engine": "adobe"
  },
  "adobe_guardrails": {
    "gates_passed": ["premium_toggle_on", "low_confidence", "structural_failures", "page_count_ok", "within_cost_caps"],
    "gates_failed": [],
    "estimated_adobe_pages": 5,
    "estimated_cost_credits": 75,
    "failure_reasons": ["Single-column collapse: 8 rows but only 1 column"]
  },
  "user_requested_premium": true
}
```

---

## ✅ Guarantees

1. **No Hidden Charges**: Adobe is NEVER used unless user explicitly enables premium toggle
2. **Cost Predictability**: Hard limits on page count (50 max)
3. **Deterministic**: Same document + same settings = same decision
4. **Transparent**: All decisions logged with reasons
5. **User Control**: Premium toggle gives users full control
6. **Structural Necessity**: Adobe only called when document has actual structural issues

---

## 🚀 Deployment Checklist

- [x] `decision_router.py`: Add guardrail methods
- [x] `docai_service.py`: Integrate guardrails
- [x] `main.py`: Extract premium flag, calculate credits
- [x] Frontend: Premium toggle implemented
- [x] Logging: Comprehensive cost tracking
- [x] Testing: Validate all 5 gates
- [ ] Deploy to Cloud Run
- [ ] Monitor Adobe usage in production

---

## 📝 Summary

This implementation ensures Adobe PDF Extract is used **ONLY** when:
1. ✅ User wants it (premium toggle ON)
2. ✅ DocAI confidence is low (< 0.75)
3. ✅ Document has structural failures (5 checks)
4. ✅ Page count is reasonable (≤ 50)
5. ✅ Within cost caps

Result: **Predictable costs, transparent pricing, happy users!** 🎉

