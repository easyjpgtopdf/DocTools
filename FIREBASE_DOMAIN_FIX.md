# Fix Firebase Unauthorized Domain Error

## Problem
```
Firebase: Error (auth/unauthorized-domain)
```

## Root Cause
easyjpgtopdf.com is not in Firebase's authorized domains list.

---

## Solution (Step-by-Step)

### Step 1: Open Firebase Console
```
1. Go to: https://console.firebase.google.com
2. Login with your Google account
3. Select your project
```

### Step 2: Navigate to Authentication Settings
```
1. Click "Authentication" in left sidebar
2. Click "Settings" tab
3. Scroll to "Authorized domains" section
```

### Step 3: Add Your Domains

**Click "Add domain" and add each of these:**

1. **Production domain:**
   ```
   easyjpgtopdf.com
   ```

2. **WWW subdomain:**
   ```
   www.easyjpgtopdf.com
   ```

3. **Vercel preview domains (for testing):**
   ```
   doc-tools-7b70zta9x-apnaonlineservics-projects.vercel.app
   doc-tools.vercel.app
   *.vercel.app
   ```

4. **Local development:**
   ```
   localhost
   127.0.0.1
   ```

### Step 4: Save Changes
```
Click "Add" for each domain
Wait for confirmation
```

### Step 5: Test
```
1. Clear browser cache
2. Go to: https://easyjpgtopdf.com
3. Click "Sign In" or "Sign Up"
4. Try to login/signup
5. Should work without error!
```

---

## Screenshots Reference

**Where to find it:**
```
Firebase Console
└── Your Project
    └── Authentication
        └── Settings
            └── Authorized domains
                └── [Add domain button]
```

---

## Common Issues

### Issue 1: Still getting error after adding domain
**Solution:**
- Clear browser cache completely
- Try incognito/private mode
- Wait 5 minutes for Firebase to propagate changes

### Issue 2: Domain not accepted
**Solution:**
- Don't include https:// or http://
- Just domain name: easyjpgtopdf.com
- No trailing slashes

### Issue 3: Localhost not working
**Solution:**
- Add both: localhost AND 127.0.0.1
- Add port if needed: localhost:3000

---

## Verification

After adding domains, you should see:
```
✓ easyjpgtopdf.com
✓ www.easyjpgtopdf.com
✓ localhost
✓ *.vercel.app
```

---

## Security Note

**These domains are SAFE to add:**
- They are YOUR domains
- Only requests from these domains can use Firebase Auth
- Protects against unauthorized access

**DO NOT add:**
- Unknown domains
- Suspicious URLs
- Domains you don't own

---

## Quick Fix Command

**If you have Firebase CLI installed:**
```bash
firebase functions:config:set authorized.domains="easyjpgtopdf.com,www.easyjpgtopdf.com,localhost"
```

**But using Firebase Console is RECOMMENDED (easier)**

---

## After Fix

**Test these pages:**
1. https://easyjpgtopdf.com/login.html
2. https://easyjpgtopdf.com/signup.html
3. https://easyjpgtopdf.com/dashboard.html

**All should work without unauthorized-domain error!**

---

**Fix Time:** 2-3 minutes
**Difficulty:** Easy
**Required Access:** Firebase Console admin
