# Environment Files - Quick Reference

## Your Current Setup ✅

```
DocTools/
├── .env                          ← Root secrets (IGNORED by Git) 🔒
├── .env.example                  ← Root template (PUBLIC) 📄
├── ENV_SETUP.md                  ← This setup guide
├── .gitignore                    ← Git security rules ✓ Updated
│
└── server/
    ├── .env                      ← Server secrets (IGNORED by Git) 🔒
    ├── .env.example              ← Server template (PUBLIC) 📄
    ├── .gitignore                ← Server safety rules ✓ Updated
    └── SETUP.md                  ← Server setup guide
```

## What's Protected ✅

| File | Location | Git | Contains | Safety |
|------|----------|-----|----------|--------|
| `.env` | Root | ❌ Ignored | Razorpay keys | 🔒 Secret |
| `.env` | server/ | ❌ Ignored | All credentials | 🔒 Secret |
| `.env.example` | Root | ✅ Tracked | Template | 📄 Public |
| `.env.example` | server/ | ✅ Tracked | Template | 📄 Public |
| `firebase-key.json` | server/ | ❌ Ignored | Firebase credentials | 🔒 Secret |

## How It Works

### When You Commit to Git:
```bash
git add .
git commit -m "message"
```
- ✅ Commits: `.env.example` files (templates for others)
- ✅ Commits: Code, HTML, CSS, JS (public)
- ❌ Ignores: `.env` files (your secrets stay safe)
- ❌ Ignores: `firebase-key.json` (never exposed)

### Result:
- Your team gets `.env.example` to copy from
- Your secret keys are NEVER pushed to GitHub
- Safe for public repositories!

## To Use This Setup

### 1. First Time (You already did this):
```bash
# Root level
cp .env.example .env
# Edit and add Razorpay keys

# Server level
cd server
cp .env.example .env
# Edit and add Razorpay keys (+ Firebase if needed)
```

### 2. When Sharing with Team:
```bash
# They clone the repo and get .env.example files
# They run:
cp .env.example .env
cp server/.env.example server/.env
# They add their own keys (if they have access)
# OR you provide them separately (never in Git)
```

### 3. For Production Deployment:
- You DON'T push `.env` to GitHub
- Add env vars directly in your hosting platform's dashboard
- (Render, Heroku, Railway, etc. all support this)

## Security Checklist ✅

- [x] `.env` files added to `.gitignore`
- [x] `.env.example` files created (as templates)
- [x] Root `.gitignore` updated with env rules
- [x] Server `.gitignore` updated with env rules
- [x] Firebase key patterns in `.gitignore`
- [x] Documentation created (`ENV_SETUP.md`)

## If Something Goes Wrong

### "I accidentally committed .env!"
```bash
# Remove it from Git history (doesn't delete local file)
git rm --cached .env
git commit -m "Remove .env from Git (was accidental)"

# Then:
# 1. Regenerate all your keys in Razorpay dashboard
# 2. Add .env to .gitignore (already done)
# 3. Push the fix
```

### "Which .env should I edit?"
- **For testing locally**: Edit `server/.env`
- **For future client features**: Edit root `.env`
- **Never edit**: `.env.example` files (they're templates)

### ".env not loading?"
- Make sure file exists: `ls -la .env` or `dir .env`
- Is dotenv installed? (It is: `npm list dotenv`)
- Restart server: `node server.js`
- Check it's not listed in `.gitignore` twice

## Files to Share

When you share your repo (GitHub, etc.):

✅ **Share (already will be):**
- `.env.example` - Template for others
- `.env.example` (server/) - Server template
- `ENV_SETUP.md` - This guide
- `SETUP.md` (server/) - Setup instructions
- `.gitignore` - Security rules

❌ **DON'T Share:**
- `.env` - Contains your secret keys
- `.env` (server/) - Contains server secrets
- `firebase-key.json` - Firebase private key
- Any file with actual credentials

## Next Steps

1. ✅ Your setup is complete!
2. ✅ All secrets are protected from Git
3. ✅ Team members can clone and copy `.env.example` to `.env`
4. ✅ Ready for deployment to production

Start server:
```bash
cd server
node server.js
```

Visit: http://localhost:3000
