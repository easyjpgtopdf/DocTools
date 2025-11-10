# Environment Variables Setup Guide

## File Structure

Your project has `.env` files in two locations. Here's the proper setup:

```
DocTools/
├── .env                          ← Root level (for client/future use)
├── .env.example                  ← Template for root (PUBLIC - commit this)
├── server/
│   ├── .env                      ← Server secrets (NEVER commit)
│   ├── .env.example              ← Template for server (PUBLIC - commit this)
│   └── SETUP.md                  ← Server setup guide
```

## What Goes Where

### Root Level: `.env`
- **Location**: `DocTools/.env`
- **Contents**: Razorpay keys (shared across all tools)
- **Commit**: ❌ NO (in `.gitignore`)
- **Copy from**: `.env.example`

```bash
# Example: DocTools/.env
RAZORPAY_KEY_ID=rzp_live_YOUR_KEY_ID_HERE
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET_HERE
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET_HERE
```

### Server Level: `server/.env`
- **Location**: `DocTools/server/.env`
- **Contents**: Razorpay keys + Firebase (if using) + Payment gateway configs
- **Commit**: ❌ NO (in `.gitignore`)
- **Copy from**: `server/.env.example`

```bash
# Example: DocTools/server/.env
RAZORPAY_KEY_ID=rzp_live_YOUR_KEY_ID_HERE
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET_HERE
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET_HERE
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}  # Optional
```

## Setup Steps

### First Time Setup

1. **At root level** (`DocTools/` folder):
   ```bash
   cp .env.example .env
   # Edit DocTools/.env and add your Razorpay keys
   ```

2. **At server level** (`DocTools/server/` folder):
   ```bash
   cp .env.example .env
   # Edit DocTools/server/.env and add your Razorpay keys
   ```

3. **Optional: Firebase** (if you need authentication):
   - Get service account JSON from Firebase Console
   - Paste it in `FIREBASE_SERVICE_ACCOUNT` in `server/.env` (as a single-line JSON string)

### For Team Members / Deployment

- **Share with team**: Send them `.env.example` files (these are PUBLIC)
- **They do**: Copy `.env.example` to `.env` and fill in their own keys
- **What to NEVER share**:
  - ❌ `.env` files (they have actual secrets)
  - ❌ Firebase private keys
  - ❌ Razorpay secret keys

## Git Ignore Rules

The `.gitignore` file (root level) has these rules:

```gitignore
# All .env files are ignored
.env
.env.local
.env.*.local
.env.prod
.env.dev
.env.test
server/.env
server/.env.local

# Firebase keys are ignored
firebase-key.json
server/firebase-key.json
*.serviceAccountKey.json
```

**This means:**
- ✅ Git will track: `.env.example`, `.env.example.*` (templates)
- ❌ Git will ignore: `.env`, `server/.env` (actual secrets)

## How to Use Env Variables

### In Client Code (JavaScript)
```javascript
// DO NOT access env variables directly in client-side code
// They would be exposed in the browser
// Instead, use API calls to the server
fetch('/api/create-order', { ... })
```

### In Server Code (Node.js)
```javascript
const razorpayKey = process.env.RAZORPAY_KEY_ID;
const razorpaySecret = process.env.RAZORPAY_KEY_SECRET;
```

The `dotenv` package (already installed in `server/package.json`) loads `.env` automatically.

## Troubleshooting

### "Razorpay order creation fails"
- Check that `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are in `server/.env`
- Verify they're the correct keys (live vs test)
- Restart the server after editing `.env`

### "Firebase error: not valid JSON"
- Make sure `FIREBASE_SERVICE_ACCOUNT` is a single-line JSON string
- No newlines or line breaks in the middle
- Paste the entire JSON from your Firebase service account file

### ".env file not being loaded"
- Make sure you're in the right folder: `server/.env` not elsewhere
- Verify the file exists: `ls -la server/.env` (Mac/Linux) or `dir server\.env` (Windows)
- Restart the server: `node server.js`

## Security Best Practices

✅ **DO:**
- Store `.env.example` templates in Git (public reference)
- Use different keys for dev/prod/staging
- Rotate Razorpay keys periodically
- Use secrets manager for production (GitHub Secrets, Render env vars, etc.)
- Add `.env` to `.gitignore` ✓ (already done)

❌ **DON'T:**
- Commit `.env` files to Git
- Share secret keys in messages or emails
- Use the same keys across environments
- Hardcode secrets in source files
- Log sensitive values to console

## For Production Deployment

When deploying to Render, Heroku, Railway, etc.:

1. Do NOT commit `.env` file
2. Add env variables in the hosting platform's dashboard:
   - Go to Environment Variables section
   - Add each variable from your `.env` file
   - Server will load them automatically (no `.env` file needed)

Example for Render:
```
RAZORPAY_KEY_ID = rzp_live_...
RAZORPAY_KEY_SECRET = ...
RAZORPAY_WEBHOOK_SECRET = ...
FIREBASE_SERVICE_ACCOUNT = {...}
```

## Questions?

Refer to:
- `server/SETUP.md` - Detailed server setup
- `.env.example` - What variables are available
- `.gitignore` - What Git ignores (for security)
