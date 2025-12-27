# Adobe PDF Extract API - Credentials Setup Guide

## कैसे प्राप्त करें Adobe API Credentials

### Step 1: Adobe Developer Console Access
1. Visit: https://developer.adobe.com/console
2. Sign in with Adobe ID (or create free account)
3. Click "Create new project"

### Step 2: Add PDF Extract API
1. In your project, click "Add API"
2. Select "PDF Services API"
3. Choose "OAuth Server-to-Server" authentication
4. Click "Save configured API"

### Step 3: Get Credentials
After setup, you'll see:
```json
{
  "client_id": "abc123def456...",
  "client_secret": "p-xyz789abc123...",
  "organization_id": "org456@AdobeOrg"
}
```

**Important**: 
- `client_id`: Public identifier (safe to log)
- `client_secret`: **SECRET** - never commit to GitHub
- Keep these credentials secure

## Security Rules

### ✅ SAFE (Allowed)
- Store in `.env` files (NOT committed to GitHub)
- Store in Cloud Run environment variables
- Store in Vercel environment variables
- Log `client_id` (public identifier)

### ❌ UNSAFE (NEVER Do)
- Commit to GitHub / version control
- Hard-code in source files
- Send to frontend/browser
- Share in public documentation
- Log `client_secret`

## Where Credentials Are Used

### Backend Only (Cloud Run)
```
pdf-to-excel-backend/
├── premium_layout/adobe_fallback_service.py  ← Uses credentials
└── .env  ← Stores credentials (NOT in GitHub)
```

### Frontend (Vercel)
```
NO ADOBE CREDENTIALS NEEDED IN FRONTEND
Frontend only calls backend API, which handles Adobe internally
```

## Current Status

- ✅ Code ready to accept credentials via environment variables
- ✅ `.gitignore` configured to exclude `.env` files
- ✅ Credentials never exposed to frontend
- ⏳ Need to add actual credentials to Cloud Run

## Next Steps

1. Get credentials from Adobe Developer Console
2. Add to Cloud Run (see DEPLOYMENT_GUIDE.md)
3. Test with a complex PDF
4. Monitor logs for Adobe fallback triggers

