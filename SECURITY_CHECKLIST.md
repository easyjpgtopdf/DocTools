# Security Checklist for EasyJpgToPDF.com

## Immediate Actions (Do Now)

### 1. Change Critical Passwords
**Why:** Good practice after setup with external help
**What to change:**
- [ ] GitHub account password
- [ ] Vercel account password  
- [ ] Firebase console password
- [ ] Razorpay dashboard password
- [ ] Namecheap account password

### 2. Enable 2FA (Two-Factor Authentication)
**Critical platforms:**
- [ ] GitHub (Settings > Password and authentication)
- [ ] Vercel (Account Settings > Security)
- [ ] Firebase (Google Account > Security)
- [ ] Razorpay (Account Settings > Security)

### 3. Revoke Old Access Tokens (If Any)
**GitHub:**
- Go to: Settings > Developer settings > Personal access tokens
- Revoke any unused tokens

**Vercel:**
- Go to: Account Settings > Tokens
- Delete any old/unused tokens

### 4. Review Authorized Applications
**GitHub:**
- Settings > Applications > Authorized OAuth Apps
- Remove any you don't recognize

**Vercel:**
- Settings > Connected Accounts
- Check what's connected

---

## Firebase Authorized Domains Fix

### Problem
```
Firebase: Error (auth/unauthorized-domain)
```

### Solution (Do This Now)

1. **Go to Firebase Console:**
   ```
   https://console.firebase.google.com
   ```

2. **Select Your Project**

3. **Go to Authentication:**
   ```
   Authentication > Settings > Authorized domains
   ```

4. **Add These Domains:**
   ```
   easyjpgtopdf.com
   www.easyjpgtopdf.com
   doc-tools-7b70zta9x-apnaonlineservics-projects.vercel.app (Vercel preview URL)
   localhost (for local testing)
   ```

5. **Click "Add Domain" for each**

6. **Save Changes**

---

## Environment Variables Audit

### Check Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Open: doc-tools project
3. Settings > Environment Variables
4. Verify these are set (don't share values):

**Payment:**
- [x] RAZORPAY_KEY_ID
- [x] RAZORPAY_KEY_SECRET
- [x] RAZORPAY_WEBHOOK_SECRET

**Firebase:**
- [x] FIREBASE_SERVICE_ACCOUNT
- [x] FIREBASE_API_KEY
- [x] FIREBASE_AUTH_DOMAIN
- [x] FIREBASE_PROJECT_ID
- [x] FIREBASE_STORAGE_BUCKET
- [x] FIREBASE_MESSAGING_SENDER_ID
- [x] FIREBASE_APP_ID

### Rotate Keys (If Concerned)

**Razorpay:**
1. Login to Razorpay Dashboard
2. Settings > API Keys
3. Generate new keys
4. Update in Vercel environment variables
5. Test payment flow

**Firebase:**
1. Go to Project Settings
2. Service Accounts tab
3. Generate new service account key
4. Update FIREBASE_SERVICE_ACCOUNT in Vercel
5. Test authentication

---

## Regular Security Maintenance

### Weekly
- [ ] Review Vercel deployment logs
- [ ] Check Firebase authentication logs
- [ ] Monitor Razorpay transactions

### Monthly
- [ ] Review GitHub repository access
- [ ] Check Vercel environment variables
- [ ] Audit Firebase security rules
- [ ] Review Razorpay API usage

### Quarterly
- [ ] Rotate API keys
- [ ] Update dependencies
- [ ] Security audit of codebase
- [ ] Review access logs

---

## What AI Assistant Had Access To

### ✅ What I Could See:
- Repository structure (files and folders)
- Code in files
- Git commits and history
- Vercel CLI commands output
- Environment variable NAMES (not values)

### ❌ What I Could NOT See:
- Environment variable VALUES (all encrypted)
- Your passwords
- API keys/secrets (stored in Vercel)
- Firebase private data
- Razorpay transaction details
- Your personal information

### 🔐 How Your Data Stayed Safe:
- All secrets in Vercel environment variables (encrypted)
- .gitignore prevented committing sensitive files
- No credentials in code
- Proper authentication flows
- Encrypted HTTPS connections

---

## Signs of Compromise (Watch For)

### Immediate Red Flags:
- [ ] Unexpected charges on Razorpay
- [ ] Unknown users in Firebase
- [ ] Unfamiliar deployments in Vercel
- [ ] Unknown commits in GitHub
- [ ] Emails about password changes you didn't make

### What to Do If Compromised:
1. Change ALL passwords immediately
2. Revoke ALL API keys
3. Generate new keys everywhere
4. Enable 2FA on all platforms
5. Contact platform support if needed

---

## Contact Information

**If You Need Help:**
- GitHub Support: https://support.github.com
- Vercel Support: https://vercel.com/support
- Firebase Support: https://firebase.google.com/support
- Razorpay Support: https://razorpay.com/support

---

## Current Status

**Last Security Review:** November 17, 2025
**Setup Completed By:** AI Assistant (no persistent access)
**Account Owner:** easyjpgtopdf (YOU)
**Security Level:** ✅ Good (with recommended improvements)

---

## Recommended Next Steps (Priority Order)

1. **URGENT:** Add domains to Firebase (fix auth error)
2. **HIGH:** Enable 2FA on all platforms
3. **MEDIUM:** Change all passwords
4. **MEDIUM:** Review and revoke old access tokens
5. **LOW:** Set up regular security reviews

**Remember:** You are the ONLY person with full admin access. Keep it that way!
