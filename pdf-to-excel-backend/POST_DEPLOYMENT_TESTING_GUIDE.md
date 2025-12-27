# 🧪 Post-Deployment Testing Guide

## 📋 Overview
This guide walks you through testing the Adobe PDF Extract API integration after deployment.

**Critical Fix Deployed**: Real Adobe API integration (replaced mock)  
**Expected Result**: Invoices, bills, and complex tables should now extract accurately

---

## ✅ PRE-TEST CHECKLIST

### 1. Verify Deployment
```bash
# Check service is running
gcloud run services describe pdf-backend --region us-central1

# Check logs for startup
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pdf-backend" --limit 20
```

### 2. Verify Adobe Credentials
```bash
# Run verification script
cd pdf-to-excel-backend
./verify-adobe-setup.ps1  # Windows
# OR
./verify-adobe-setup.sh   # Linux/Mac
```

Expected output:
```
✅ ADOBE_CLIENT_ID: Set (value hidden)
✅ ADOBE_CLIENT_SECRET: Set (value hidden for security)
```

### 3. Verify Feature Flags
Look for this in logs:
```
FEATURE FLAGS CONFIGURATION
  ADOBE_ENABLED: True
  QA_VALIDATION_ENABLED: True
```

---

## 🧪 TEST SCENARIOS

### **Test 1: Simple Invoice (Critical Test)**

**Purpose**: Verify Adobe API extracts invoice line items

**Test PDF**: Any invoice with table structure (items, qty, price, total)

**Steps**:
1. Go to your frontend: https://your-frontend-url.vercel.app
2. Upload invoice PDF
3. **Enable "High Accuracy Mode (Premium)" toggle** ✅
4. Click convert
5. Wait for completion

**Expected Result**:
- ✅ Conversion completes successfully
- ✅ Download shows Excel file with invoice data
- ✅ **NOT "no data" or blank cells**
- ✅ Line items in separate rows
- ✅ Columns: Item, Quantity, Price, Amount
- ✅ Subtotal, tax, total in footer

**Expected Logs** (Cloud Logging):
```
🚀 Calling REAL Adobe PDF Extract API...
Requesting new Adobe API access token...
✅ Adobe access token obtained (expires in 3600s)
Uploading PDF asset: document.pdf (123456 bytes)
✅ PDF uploaded successfully
Starting PDF extraction for asset: urn:aaid:AS:xxx
Job status: in progress (poll 1/60)
Job status: done (poll 3/60)
✅ Extraction complete (from ZIP)!
✅ Adobe API returned structured data
Processing table element: //Document/Table
✅ Processed table: //Document/Table (15 rows × 5 cols)
✅ Adobe SUCCESS: Replacing 1 DocAI layouts with 1 Adobe layouts
QA Validation: PASS
```

**Expected Response**:
```json
{
  "status": "success",
  "layout_source": "adobe",
  "creditsDeducted": 75,
  "creditPerPage": 15.0,
  "qa_status": "PASS",
  "engine_chain": ["docai", "adobe"]
}
```

**If Test FAILS**:
- Check if premium toggle was enabled
- Check logs for Adobe API errors
- Verify credentials are correct
- Check Adobe API status: https://status.adobe.com/

---

### **Test 2: Complex Table with Merges**

**Purpose**: Verify merged cells are handled correctly

**Test PDF**: Table with:
- Multi-row headers
- Merged cells
- Complex structure

**Steps**:
1. Upload PDF with complex table
2. Enable premium toggle
3. Convert
4. Download Excel

**Expected Result**:
- ✅ Merged cells rendered correctly
- ✅ Headers span multiple columns/rows as in PDF
- ✅ Data cells aligned properly
- ✅ Better structure than DocAI-only conversion

**Key Log Pattern**:
```
Merged cells: 8
Header rows: [0, 1]
Locked columns: 5
```

---

### **Test 3: Bank Statement**

**Purpose**: Verify transaction tables extracted

**Test PDF**: Bank statement with transactions

**Expected Result**:
- ✅ Date column
- ✅ Description column
- ✅ Debit/Credit columns
- ✅ Balance column
- ✅ All transactions in separate rows

---

### **Test 4: Standard Mode (DocAI Only)**

**Purpose**: Verify DocAI still works when premium OFF

**Steps**:
1. Upload simple table PDF
2. **Keep premium toggle OFF** ❌
3. Convert

**Expected Result**:
- ✅ Conversion uses DocAI
- ✅ Standard pricing (5 credits/page)
- ✅ No Adobe logs
- ✅ Response: `"layout_source": "docai"`

**Expected Logs**:
```
Adobe fallback NOT triggered: User did not enable premium mode
```

---

### **Test 5: Guardrails Test (High Confidence)**

**Purpose**: Verify Adobe not used when not needed

**Test PDF**: Simple, well-structured table

**Steps**:
1. Upload clean table PDF
2. Enable premium toggle
3. Convert

**Expected Result**:
- ✅ DocAI used (high confidence, no structural failures)
- ✅ Standard pricing (5 credits/page)
- ✅ Response: `"layout_source": "docai"`

**Expected Logs**:
```
ADOBE FALLBACK GUARDRAILS CHECK
Adobe fallback allowed: NO
Reason: Document AI confidence 0.85 >= 0.75 - Adobe not needed
Gates failed: high_confidence
```

---

### **Test 6: Multi-Page Invoice**

**Purpose**: Verify cost calculation for multi-page Adobe

**Test PDF**: 3-page invoice

**Expected Result**:
- ✅ All 3 pages converted
- ✅ Credits: 3 × 15 = 45 credits
- ✅ Response shows correct page count
- ✅ All pages in separate Excel sheets

**Cost Verification**:
```json
{
  "pagesProcessed": 3,
  "creditsDeducted": 45,
  "creditPerPage": 15.0,
  "pricing": {
    "engine": "adobe",
    "total_cost": 45
  }
}
```

---

### **Test 7: Error Handling (Invalid PDF)**

**Purpose**: Verify graceful failure

**Test PDF**: Corrupted or image-only PDF

**Expected Result**:
- ✅ Adobe tries extraction
- ✅ If Adobe fails, fallback to DocAI
- ✅ No system crash
- ✅ User gets result (even if limited)

**Expected Logs**:
```
Adobe API call failed: <error details>
Auto-fallback to DocAI: ENABLED
Returning Document AI result
```

---

## 📊 VERIFICATION CHECKLIST

After running all tests, verify:

### Adobe API Integration
- [ ] OAuth token obtained successfully
- [ ] PDF uploaded to Adobe cloud
- [ ] Extraction job submitted and completed
- [ ] Result downloaded and parsed
- [ ] No mock data warnings in logs

### Data Quality
- [ ] Invoices show actual line items (not "no data")
- [ ] Complex tables have correct structure
- [ ] Merged cells rendered properly
- [ ] Headers detected and styled
- [ ] Unicode text (Hindi, etc.) preserved

### Cost Tracking
- [ ] Adobe conversions charged 15 credits/page
- [ ] DocAI conversions charged 5 credits/page
- [ ] Multi-page pricing calculated correctly
- [ ] User sees correct credits deducted

### Guardrails
- [ ] Premium toggle controls Adobe usage
- [ ] High-confidence docs use DocAI
- [ ] Structural failures trigger Adobe
- [ ] Page limits enforced (max 50 pages)
- [ ] Feature flags respected

### QA Validation
- [ ] QA status in response (PASS/WARN/FAIL)
- [ ] Warnings logged for quality issues
- [ ] Determinism hash generated
- [ ] Engine chain tracked

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Issue 1: "Adobe credentials not configured"

**Symptom**: Logs show Adobe not available  
**Solution**:
```bash
cd pdf-to-excel-backend
./add-adobe-credentials.ps1  # Re-run credential setup
```

### Issue 2: "Adobe API returned no data"

**Symptom**: Adobe called but returns empty  
**Cause**: PDF format not supported by Adobe  
**Solution**: Falls back to DocAI automatically

### Issue 3: "Job polling timed out"

**Symptom**: Adobe extraction takes > 5 minutes  
**Cause**: Very complex or large PDF  
**Solution**: System auto-falls back to DocAI

### Issue 4: "Premium toggle not working"

**Symptom**: Adobe not called even with toggle ON  
**Check**:
- Verify `user_wants_premium` in request logs
- Check if confidence > 0.75 (no Adobe needed)
- Check if structural failures detected

### Issue 5: "Credits deducted but poor quality"

**Symptom**: Adobe used but output still poor  
**Check**:
- Verify PDF is not scanned image (OCR needed first)
- Check if PDF has extractable text
- Review Adobe extraction result in logs

---

## 📝 LOG MONITORING

### Key Log Patterns to Watch

**Success Pattern**:
```
🚀 Calling REAL Adobe PDF Extract API
✅ Adobe access token obtained
✅ PDF uploaded successfully
Job status: done
✅ Extraction complete
✅ Processed table
✅ Adobe SUCCESS
QA STATUS: PASS
```

**Fallback Pattern**:
```
Adobe API call failed: <reason>
⚠️ Adobe fallback returned no layouts
Falling back to Document AI results
```

**Guardrail Block Pattern**:
```
Adobe fallback NOT triggered: <reason>
Gates failed: <gate_name>
Using Document AI result
```

### Search Queries for Cloud Logging

**Adobe API Calls**:
```
resource.type="cloud_run_revision"
resource.labels.service_name="pdf-backend"
"Adobe PDF Extract API"
```

**Adobe Success**:
```
resource.type="cloud_run_revision"
"Adobe SUCCESS"
```

**Adobe Failures**:
```
resource.type="cloud_run_revision"
"Adobe" AND ("failed" OR "error")
```

**QA Validation**:
```
resource.type="cloud_run_revision"
"QA Validation:"
```

---

## 🎯 SUCCESS CRITERIA

All tests pass if:
1. ✅ Invoices extract line items (no "no data")
2. ✅ Complex tables better than DocAI
3. ✅ Adobe actually called (visible in logs)
4. ✅ Guardrails prevent unnecessary Adobe usage
5. ✅ Cost tracking accurate
6. ✅ Fallback works on errors
7. ✅ QA validation active
8. ✅ Unicode text preserved

---

## 📞 ESCALATION

**If Multiple Tests Fail**:
1. Check Adobe API status: https://status.adobe.com/
2. Verify credentials: Run `verify-adobe-setup.ps1`
3. Check Cloud Run logs for errors
4. Roll back if needed:
   ```bash
   gcloud run services update-traffic pdf-backend --to-revisions=PREVIOUS_REVISION=100
   ```

**Emergency Adobe Disable**:
```bash
gcloud run services update pdf-backend --set-env-vars="ADOBE_ENABLED=false" --region us-central1
```

---

## 📊 REPORT TEMPLATE

After testing, document results:

```
# Adobe PDF Extract API Integration Test Report
Date: [DATE]
Tester: [NAME]
Environment: Production

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| Simple Invoice | ✅/❌ | [details] |
| Complex Table | ✅/❌ | [details] |
| Bank Statement | ✅/❌ | [details] |
| Standard Mode | ✅/❌ | [details] |
| Guardrails | ✅/❌ | [details] |
| Multi-Page | ✅/❌ | [details] |
| Error Handling | ✅/❌ | [details] |

## Adobe API Performance
- Success Rate: X%
- Average Extraction Time: X seconds
- Fallback Rate: X%

## Data Quality
- Invoice Accuracy: [notes]
- Table Structure: [notes]
- Merged Cells: [notes]

## Cost Tracking
- Credits Deducted: Correct ✅ / Incorrect ❌
- Pricing Model: Working ✅ / Issues ❌

## Issues Found
[List any issues]

## Recommendation
- [ ] Proceed to full production
- [ ] Fix issues first
- [ ] Roll back
```

---

**Last Updated**: December 27, 2025  
**Version**: 1.0.0  
**Status**: Ready for Testing

