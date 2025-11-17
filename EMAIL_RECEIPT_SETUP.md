# Email Receipt Setup Guide

## 📧 Email Service Configuration

### Service: Resend (Free Tier - 100 emails/day)

---

## 🚀 Setup Steps

### 1. Create Resend Account
1. Go to: https://resend.com/signup
2. Sign up with your email
3. Verify your email address

### 2. Get API Key
1. Login to: https://resend.com/api-keys
2. Click "Create API Key"
3. Name: `easyjpgtopdf-production`
4. Permissions: **Full Access** (default)
5. Copy the API key (starts with `re_...`)
   - **IMPORTANT:** Save it immediately, you won't see it again!

### 3. Verify Domain (Optional but Recommended)

**Option A: Use Resend's Domain (Quick Start)**
- From: `noreply@resend.dev`
- No verification needed
- Limited to 100 emails/day
- **Works immediately!**

**Option B: Use Custom Domain (Professional)**
1. Go to: https://resend.com/domains
2. Click "Add Domain"
3. Enter: `easyjpgtopdf.com`
4. Add DNS Records (from Namecheap):
   - Type: `TXT`
   - Host: `@`
   - Value: (provided by Resend)
   
   - Type: `CNAME`
   - Host: `resend._domainkey`
   - Value: (provided by Resend)

5. Wait for verification (5-10 minutes)
6. Update code: Change from address to `noreply@easyjpgtopdf.com`

### 4. Add Environment Variable to Vercel

1. Go to: https://vercel.com/easyjpgtopdf/doctools/settings/environment-variables
2. Click "Add New"
3. Fill in:
   - **Key:** `RESEND_API_KEY`
   - **Value:** `re_xxxxxxxxxxxxx` (your API key)
   - **Environment:** Production, Preview, Development (all)
4. Click "Save"

### 5. Redeploy (Automatic)
- Next git push will trigger deployment with new env var
- Or manually: `vercel --prod` (if needed)

---

## 🧪 Testing

### Test Email Flow:
1. Login to https://easyjpgtopdf.com
2. Go to donation section
3. Enter amount: ₹10
4. Complete payment (test mode if available)
5. Check your email inbox
6. Should receive: **"Payment Receipt - Transaction pay_..."**

### Expected Email Content:
- Subject: `Payment Receipt - Transaction pay_ABC123...`
- From: `easyjpgtopdf <noreply@resend.dev>` (or your domain)
- To: Your Gmail account
- Contains:
  - ✓ Success header
  - Transaction ID
  - Order ID
  - Date & Time
  - Payment Method
  - Amount
  - Button to view full receipt online
  - Company footer

---

## 📊 Email Delivery Status

### Check Resend Dashboard:
1. Go to: https://resend.com/emails
2. See all sent emails
3. Status indicators:
   - ✅ **Delivered** - Email sent successfully
   - ⏳ **Queued** - In sending queue
   - ❌ **Failed** - Check error details

### Logs:
- Click on any email to see:
  - Delivery time
  - Recipient
  - Open/click tracking (if enabled)
  - Error details (if failed)

---

## 🔧 Code Changes Made

### 1. API Endpoint: `/api/send-receipt-email.js`
- Sends HTML email using Resend API
- Validates email format
- Creates beautiful receipt template
- Returns email ID on success

### 2. Frontend: `js/donate.js`
- Payment success handler now sends email
- Calls `/api/send-receipt-email` endpoint
- Shows status: "Sending receipt email..."
- Continues to receipt page even if email fails

### 3. Configuration: `vercel.json`
- Added rewrite rule for email API
- Route: `/api/send-receipt-email` → `/api/send-receipt-email.js`

---

## 🎨 Email Template Features

### Design:
- ✓ Professional gradient header (purple)
- ✓ Success checkmark icon
- ✓ Responsive design (mobile-friendly)
- ✓ Complete payment details
- ✓ Button to view online receipt
- ✓ Company branding
- ✓ Footer with links

### Content:
- Personalized greeting (user's name)
- Thank you message
- Complete transaction details
- Important note to save email
- Link to online receipt
- Support message
- Automated email notice

---

## 💰 Pricing (Resend)

### Free Tier:
- **100 emails/day**
- **3,000 emails/month**
- Free forever
- No credit card required

### If You Need More:
- **Pro Plan:** $20/month
  - 50,000 emails/month
  - Custom domain included
  - Advanced analytics

**Your Usage Estimate:**
- Average: 10-50 payments/day = 10-50 emails/day
- Well within free tier! ✅

---

## 🔒 Security Best Practices

### 1. API Key Security:
- ✅ Stored in Vercel environment variables (encrypted)
- ✅ Never committed to Git
- ✅ Not visible in frontend code
- ✅ Only backend can access

### 2. Email Validation:
- ✅ Regex check before sending
- ✅ Resend validates recipient
- ✅ Prevents spam/abuse

### 3. Error Handling:
- ✅ Graceful failures (receipt page still works)
- ✅ Logs errors for debugging
- ✅ User-friendly error messages

---

## ❓ Troubleshooting

### Email Not Received?

**Check 1: Spam Folder**
- Resend emails sometimes go to spam initially
- Mark as "Not Spam" to train Gmail

**Check 2: Resend Dashboard**
- Check delivery status
- Look for error messages

**Check 3: Vercel Logs**
- Go to: https://vercel.com/easyjpgtopdf/doctools/deployments
- Click latest deployment
- Check function logs for errors

**Check 4: Environment Variable**
- Verify `RESEND_API_KEY` is set in Vercel
- Check it starts with `re_`

### Common Errors:

**"Email service not configured"**
- `RESEND_API_KEY` missing in Vercel
- Redeploy after adding env var

**"Invalid email address"**
- Check user's Gmail format
- Ensure email validation passes

**"Resend API error: 403"**
- API key invalid or expired
- Generate new API key

**"Resend API error: 429"**
- Rate limit exceeded (100/day)
- Wait 24 hours or upgrade plan

---

## 📝 Environment Variables Summary

**Total: 11 Environment Variables**

1. `RAZORPAY_KEY_ID`
2. `RAZORPAY_KEY_SECRET`
3. `RAZORPAY_WEBHOOK_SECRET`
4. `FIREBASE_SERVICE_ACCOUNT`
5. `FIREBASE_API_KEY`
6. `FIREBASE_AUTH_DOMAIN`
7. `FIREBASE_PROJECT_ID`
8. `FIREBASE_STORAGE_BUCKET`
9. `FIREBASE_MESSAGING_SENDER_ID`
10. `FIREBASE_APP_ID`
11. **`RESEND_API_KEY`** ← NEW!

All stored securely in Vercel (encrypted at rest).

---

## 🎯 Next Steps

1. ✅ Sign up for Resend
2. ✅ Get API key
3. ✅ Add to Vercel env vars
4. ✅ Deploy (automatic on next push)
5. ✅ Test with ₹10 payment
6. ✅ Check email inbox
7. ✅ Verify receipt looks good
8. 🎉 Done!

---

**Need Help?**
- Resend Docs: https://resend.com/docs
- Resend Support: support@resend.com
- Check Vercel logs for backend errors
- Check browser console for frontend errors
