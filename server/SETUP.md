# Server Setup Guide

## Environment Variables

This server uses environment variables for configuration. Follow the steps below to set them up.

### 1. Copy `.env.example` to `.env`

```bash
cp .env.example .env
```

### 2. Firebase Configuration (Optional but Recommended)

#### If you want to use Firebase for authentication and payments recording:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** > **Service Accounts** tab
4. Click **Generate New Private Key**
5. This downloads a JSON file with your service account credentials
6. Copy the **entire JSON content** from that file
7. In `.env`, replace the `FIREBASE_SERVICE_ACCOUNT` line with:
   ```
   FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"your-project-id",...}
   ```
   (It's all one long line - paste the entire JSON as a single line)

**⚠️ IMPORTANT:**
- **NEVER commit `.env` file to Git** (it's in `.gitignore`)
- **NEVER share your Firebase private key with anyone**
- Store it securely, preferably in a secrets manager like:
  - GitHub Secrets (for CI/CD)
  - Render/Heroku environment variables (for hosting)
  - AWS Secrets Manager
  - Google Secret Manager

#### If you skip Firebase:
- Leave `FIREBASE_SERVICE_ACCOUNT=` empty
- The server will use Application Default Credentials (ADC)
- ADC works on Google Cloud environments automatically
- Locally, you can authenticate via `gcloud auth application-default login`

### 3. Razorpay Configuration

1. Get your keys from [Razorpay Dashboard](https://dashboard.razorpay.com/app/settings/api-keys)
2. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_live_YOUR_KEY_ID
   RAZORPAY_KEY_SECRET=YOUR_SECRET_KEY
   RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET
   ```

### 4. (Optional) Stripe Configuration

If you want to support Stripe payments:
1. Get your secret key from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_SUCCESS_URL=https://yourdomain.com/donate-success
   STRIPE_CANCEL_URL=https://yourdomain.com/donate-cancelled
   ```

### 5. (Optional) PayU Configuration

If you want to support PayU payments:
1. Get your PayU credentials
2. Add to `.env`:
   ```
   PAYU_KEY=your_key
   PAYU_SALT=your_salt
   PAYU_ENV=production
   ```

## Running the Server

### Local Development

```bash
# Install dependencies
npm install

# Make sure .env file is configured
# Then run the server
node server.js

# Or use nodemon for auto-reload during development
npm install -g nodemon
nodemon server.js
```

Server will start on `http://localhost:3000` (or the PORT from `.env`)

### Production (Render, Railway, Heroku, etc.)

1. Add environment variables in your hosting platform's dashboard
2. Deploy the code (`.env` file is git-ignored, so it won't be committed)
3. The server will load env vars from the platform's configuration

## Security Checklist

- [ ] `.env` file is in `.gitignore` ✓ (already configured)
- [ ] Never commit `.env` to Git
- [ ] Firebase service account key is kept private
- [ ] Razorpay secret key is kept private
- [ ] Use HTTPS in production (required for Razorpay webhooks)
- [ ] Configure Razorpay webhook URL on their dashboard
- [ ] For webhooks, set `RAZORPAY_WEBHOOK_SECRET` to the secret shown on Razorpay dashboard

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/create-order` - Create Razorpay order (for donations without auth)
- `POST /api/payments/razorpay/order` - Create Razorpay order (authenticated)
- `POST /api/payments/payu/order` - Create PayU order (authenticated)
- `POST /api/payments/create-donation-session` - Create Stripe session (authenticated)
- `POST /api/payments/razorpay/webhook` - Razorpay webhook endpoint

## Troubleshooting

### "FIREBASE_SERVICE_ACCOUNT is not valid JSON"

This means:
1. You pasted a file path instead of JSON content
2. The JSON string is incomplete or malformed

**Solution:**
- Copy the **entire JSON file content** (from the `.json` file you downloaded from Firebase)
- Paste it as a single line in `FIREBASE_SERVICE_ACCOUNT=...`
- No newlines or extra spaces in the middle

### "Address already in use :::3000"

Another process is using port 3000.

**Solution:**
```bash
# Kill the process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use a different port
PORT=5600 node server.js
```

### Razorpay order creation fails

- Check that `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are set in `.env`
- Make sure they're live keys (not test keys) for production
- Check Razorpay dashboard for any API errors

### Firebase not working

- If you leave `FIREBASE_SERVICE_ACCOUNT=` empty, make sure you authenticate locally:
  ```bash
  gcloud auth application-default login
  ```
- Or set the env var properly with valid JSON

## Files to Know

- `.env` - Your secrets (DO NOT COMMIT)
- `.env.example` - Template showing what variables you need
- `.gitignore` - Prevents `.env` from being committed
- `server.js` - Main server file
- `firebase-key.json` - If you save the JSON file separately (also in `.gitignore`)

## Next Steps

1. Copy `.env.example` to `.env`
2. Fill in your Razorpay keys
3. (Optional) Add Firebase service account JSON
4. Run `npm install && node server.js`
5. Test: `curl http://localhost:3000/api/health`
