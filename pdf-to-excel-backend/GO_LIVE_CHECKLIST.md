# 🚀 Go-Live Checklist: Enterprise PDF → Excel System

## 📋 Overview
This checklist ensures the PDF to Excel system is production-ready with Adobe PDF Extract integration, comprehensive QA validation, and enterprise-grade safety controls.

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### 1. Environment Configuration

#### Cloud Run Environment Variables
- [ ] `DOCAI_PROJECT_ID` is set
- [ ] `DOCAI_LOCATION` is set
- [ ] `DOCAI_PROCESSOR_ID` is set
- [ ] `ADOBE_CLIENT_ID` is set (if using Adobe)
- [ ] `ADOBE_CLIENT_SECRET` is set (if using Adobe)
- [ ] `GCS_BUCKET_NAME` is set
- [ ] `DATABASE_URL` is set (if using database)

#### Feature Flags (Optional - can use defaults)
- [ ] `ADOBE_ENABLED=true` (or false to disable Adobe entirely)
- [ ] `ADOBE_CONFIDENCE_THRESHOLD=0.75`
- [ ] `MAX_ADOBE_PAGES_PER_DOC=50`
- [ ] `MAX_ADOBE_DOCS_PER_DAY=10`
- [ ] `MAX_ADOBE_PAGES_PER_DAY=150`
- [ ] `QA_VALIDATION_ENABLED=true`
- [ ] `QA_STRICT_MODE=false` (set to true for maximum safety)
- [ ] `ADOBE_AUTO_FALLBACK=true`
- [ ] `DETAILED_COST_LOGGING=true`
- [ ] `AUDIT_TRAIL_ENABLED=true`

---

### 2. Code Deployment

- [ ] All STEP 4 changes deployed (Cost Guardrails)
- [ ] All STEP 5 changes deployed (QA Matrix & Safety)
- [ ] Frontend premium toggle deployed
- [ ] Feature flags module deployed
- [ ] QA validator module deployed
- [ ] Latest commit hash: `_____________`

---

### 3. Adobe PDF Extract Setup

- [ ] Adobe credentials obtained from Adobe Developer Console
- [ ] Credentials added to Cloud Run via setup scripts
- [ ] Verified with `verify-adobe-setup.ps1`
- [ ] Test API call successful
- [ ] Billing account set up with Adobe

---

### 4. Testing (MANDATORY)

#### Functional Tests
- [ ] **Test 1**: Upload simple table PDF with premium OFF
  - Expected: DocAI used, 5 credits/page
  - Actual: __________

- [ ] **Test 2**: Upload simple table PDF with premium ON
  - Expected: DocAI used (high confidence, no structural failures)
  - Actual: __________

- [ ] **Test 3**: Upload complex table PDF with premium ON
  - Expected: Check all 5 gates, use Adobe if failures detected
  - Actual: __________

- [ ] **Test 4**: Upload well-structured complex PDF
  - Expected: DocAI used (no structural failures)
  - Actual: __________

- [ ] **Test 5**: Upload malformed table PDF with premium ON
  - Expected: Adobe used (structural failures detected)
  - Actual: __________

- [ ] **Test 6**: Upload 51-page PDF with premium ON
  - Expected: DocAI used (exceeds 50-page limit)
  - Actual: __________

#### Cost Tests
- [ ] 5-page DocAI conversion = 25 credits ✅
- [ ] 5-page Adobe conversion = 75 credits ✅
- [ ] 15-page DocAI conversion = 60 credits ✅
- [ ] 15-page Adobe conversion = 175 credits ✅

#### QA Validation Tests
- [ ] QA status = PASS for successful conversions
- [ ] QA status = WARN for quality issues
- [ ] QA status = FAIL for critical errors (if QA_STRICT_MODE=true)
- [ ] QA warnings logged for single-column collapse
- [ ] QA errors logged for cost limit violations

#### Feature Flag Tests
- [ ] Set `ADOBE_ENABLED=false` → Adobe not used
- [ ] Set `ADOBE_CONFIDENCE_THRESHOLD=0.9` → Adobe used more often
- [ ] Set `MAX_ADOBE_PAGES_PER_DOC=10` → Large docs rejected
- [ ] Set `QA_STRICT_MODE=true` → Conversions blocked on FAIL

#### Fallback Safety Tests
- [ ] Simulate Adobe API failure → Fallback to DocAI successful
- [ ] Simulate Adobe timeout → Fallback to DocAI successful
- [ ] Simulate Adobe rate limit → Fallback to DocAI successful

---

### 5. Security Checks

- [ ] Adobe credentials NOT in code
- [ ] Adobe credentials NOT in GitHub repo
- [ ] Adobe credentials NOT visible in frontend
- [ ] Adobe credentials only in Cloud Run env vars
- [ ] Credentials retrieved via `os.getenv()` only
- [ ] No secrets in logs
- [ ] No secrets in response JSON

---

### 6. Monitoring & Logging

- [ ] Cloud Logging enabled for Cloud Run
- [ ] All Adobe decisions logged with reasons
- [ ] Gates passed/failed visible in logs
- [ ] Credit calculations logged
- [ ] Structural failures logged
- [ ] QA validation results logged
- [ ] Feature flag values logged at startup

#### Sample Log Search Queries
```
# Adobe usage
jsonPayload.message:"ADOBE FALLBACK: Starting extraction"

# QA validation
jsonPayload.message:"QA Validation:"

# Cost calculation
jsonPayload.message:"CREDIT CALCULATION"

# Feature flags
jsonPayload.message:"FEATURE FLAGS CONFIGURATION"

# Errors
severity="ERROR"
```

---

### 7. Cost Control Verification

- [ ] Max 50 pages per Adobe document enforced
- [ ] Daily Adobe limits configured (per-user tracking future)
- [ ] Credit calculation matches actual engine used
- [ ] No hidden charges (Adobe only with premium toggle)
- [ ] User sees actual credits deducted

---

### 8. User Experience

- [ ] Premium toggle visible before conversion
- [ ] Tooltip shows pricing (Hindi + English)
- [ ] Result shows engine used
- [ ] Result shows accuracy level
- [ ] Result shows credits used
- [ ] Result shows credits remaining
- [ ] Adobe warning displayed when Adobe used
- [ ] No confusing error messages

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Deploy Backend to Cloud Run

```bash
# From DocTools root directory
cd pdf-to-excel-backend

# Build and deploy
gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/pdf-backend
gcloud run deploy pdf-backend \
  --image gcr.io/easyjpgtopdf-de346/pdf-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300s \
  --set-env-vars="ADOBE_ENABLED=true,QA_VALIDATION_ENABLED=true"
```

### Step 2: Deploy Frontend to Vercel

```bash
# Vercel will auto-deploy on git push to main
git push origin main

# Or manual deploy:
vercel --prod
```

### Step 3: Verify Deployment

```bash
# Check Cloud Run service is running
gcloud run services describe pdf-backend --region us-central1

# Check environment variables (values hidden)
gcloud run services describe pdf-backend --region us-central1 --format="value(spec.template.spec.containers[0].env)"

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pdf-backend" --limit 50
```

---

## 🔍 POST-DEPLOYMENT VALIDATION

### Immediate Checks (within 1 hour)

- [ ] Health check endpoint responds: `GET /health`
- [ ] Feature flags logged at startup
- [ ] First test conversion successful (DocAI)
- [ ] First Adobe conversion successful (if premium enabled)
- [ ] QA validation running without errors
- [ ] Logs showing detailed cost tracking
- [ ] No error spikes in Cloud Logging

### 24-Hour Checks

- [ ] No unexpected Adobe usage
- [ ] Cost tracking accurate
- [ ] No QA validation failures
- [ ] User complaints = 0
- [ ] Average conversion time < 30s
- [ ] Adobe fallback rate < 10%

### 7-Day Checks

- [ ] Cost projections match actual
- [ ] Adobe usage within budget
- [ ] User satisfaction high
- [ ] System stability good (uptime > 99%)
- [ ] No security incidents

---

## 🚨 EMERGENCY PROCEDURES

### Instant Adobe Disable (if needed)

#### Method 1: Environment Variable (requires redeploy)
```bash
gcloud run services update pdf-backend \
  --region us-central1 \
  --set-env-vars="ADOBE_ENABLED=false"
```

#### Method 2: Admin API (future)
```bash
curl -X POST https://your-backend-url/admin/disable-adobe \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### Method 3: Code-level (immediate, no redeploy needed)
Contact on-call engineer to call `disable_adobe_immediately()` function.

### Rollback Procedure

```bash
# Rollback to previous Cloud Run revision
gcloud run services update-traffic pdf-backend \
  --region us-central1 \
  --to-revisions=pdf-backend-00042-abc=100

# Verify rollback
gcloud run services describe pdf-backend --region us-central1
```

### Incident Response

1. **High Adobe Cost Alert**:
   - Check logs for unexpected Adobe usage
   - Verify feature flags are correct
   - Check if structural failure detection is too aggressive
   - Consider lowering `ADOBE_CONFIDENCE_THRESHOLD`

2. **QA Validation Failures**:
   - Check QA logs for failure reasons
   - Verify layouts are being generated correctly
   - Check if `QA_STRICT_MODE` is too strict
   - Temporarily disable QA strict mode if needed

3. **Conversion Failures**:
   - Check Cloud Run logs
   - Verify DocAI is responding
   - Check Adobe API status
   - Verify fallback to DocAI is working

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ Uptime: > 99%
- ✅ Average conversion time: < 30s
- ✅ Adobe fallback rate: < 10%
- ✅ QA validation failure rate: < 1%
- ✅ Error rate: < 0.5%

### Business Metrics
- ✅ User satisfaction: > 4.5/5
- ✅ Premium adoption: > 20%
- ✅ Adobe cost per conversion: within budget
- ✅ Credit deduction accuracy: 100%

### Quality Metrics
- ✅ Correct rows/columns: > 95%
- ✅ Proper merged cells: > 90%
- ✅ Stable column boundaries: > 95%
- ✅ Deterministic behavior: 100%

---

## 🎯 GO/NO-GO DECISION

### GO Criteria (ALL must be YES)

- [ ] All environment variables configured
- [ ] All functional tests passed
- [ ] All cost tests passed
- [ ] All security checks passed
- [ ] Feature flags working correctly
- [ ] QA validation working correctly
- [ ] Monitoring & logging configured
- [ ] Emergency procedures documented
- [ ] Rollback procedure tested

### NO-GO Criteria (ANY is YES → delay launch)

- [ ] Any functional test failed
- [ ] Adobe credentials exposed
- [ ] Cost calculation incorrect
- [ ] QA validation not working
- [ ] Feature flags not working
- [ ] Monitoring not configured
- [ ] Rollback procedure not tested

---

## 📝 SIGN-OFF

**Development Lead**: ________________ Date: ______

**QA Lead**: ________________ Date: ______

**DevOps Lead**: ________________ Date: ______

**Product Owner**: ________________ Date: ______

---

## 🎉 LAUNCH!

Once all checks pass and sign-offs are complete:

```
🚀 SYSTEM IS GO FOR PRODUCTION LAUNCH! 🚀
```

**Launch Date**: ______________

**Launch Time**: ______________

**On-Call Engineer**: ______________

**Monitoring URL**: ______________

---

## 📖 Additional Resources

- [Cost Guardrails Implementation](./COST_GUARDRAILS_IMPLEMENTATION.md)
- [Complete Implementation Summary](./COMPLETE_IMPLEMENTATION_SUMMARY.md)
- [Adobe Credentials Setup](./ADOBE_COMPLETE_SETUP_GUIDE.md)
- [Premium Toggle Implementation](./PREMIUM_TOGGLE_IMPLEMENTATION.md)

---

**Last Updated**: December 27, 2025
**Version**: 1.0.0
**Status**: READY FOR GO-LIVE VALIDATION

