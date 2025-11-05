# Firebase Setup (easyjpgtopdf.com)

This guide prepares Firebase Functions + Cloud Messaging for **easyjpgtopdf.com**.

---

## 1. Prerequisites

1. **Firebase project** created in Google Cloud console (you already enabled Cloud Messaging API v1).
2. **Firebase CLI** installed:
   ```powershell
   npm install -g firebase-tools
   ```
3. **Node.js 18+** (Cloud Functions default runtime is Node 20).
4. **Service account / API key** for server-side use (store as GitHub secret later).

---

## 2. Authenticate CLI

```powershell
firebase login
```
- Opens browser → sign into same Google account as Firebase project.

Optional (for CI/CD without browser):
```powershell
firebase login:ci
```
Copy the token and save as `FIREBASE_TOKEN` secret in GitHub.

---

## 3. Initialize functions workspace

From repo root:
```powershell
cd services/firebase
firebase init functions \
  --project <YOUR_PROJECT_ID> \
  --language typescript \
  --node 20 \
  --eslint \
  --force
```
This will:
- Create `.firebaserc`, `firebase.json`.
- Scaffold `functions/` with `package.json`, `tsconfig.json`, `src/index.ts`.

> If you prefer JavaScript, rerun with `--language javascript`.

Commit the generated files (except `functions/node_modules`).

---

## 4. Sample environment variables

Use `functions/.env` for local emulators and Firebase config for production.

Example `.env` (do **NOT** commit):
```
FIREBASE_EMULATOR=true
RENDER_WEBHOOK_SECRET=your-secret
CLOUD_RUN_BASE_URL=https://pdf-word-<region>-a.run.app
```

Prod secrets:
- Set via `firebase functions:config:set key=value` or Google Cloud Console → Secret Manager.
- Access inside functions with `process.env.KEY` or `functions.config().group.key`.

---

## 5. Local development

```powershell
cd services/firebase
npm install --prefix functions
firebase emulators:start --only functions
```
- Hitting `http://localhost:5001/<project>/us-central1/<functionName>` invokes the emulator.

---

## 6. Deploy workflow

Manual deploy:
```powershell
firebase deploy --only functions
```

CI/CD via GitHub Actions (add in `.github/workflows/firebase.yml`):
```yaml
name: Deploy Firebase Functions
on:
  push:
    paths:
      - 'services/firebase/**'
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g firebase-tools
      - run: npm install --prefix services/firebase/functions
      - run: firebase deploy --only functions --project ${{ secrets.FIREBASE_PROJECT_ID }}
        env:
          FIREBASE_TOKEN: ${{ secrets.FIREBASE_TOKEN }}
```
Configure secrets `FIREBASE_TOKEN` and `FIREBASE_PROJECT_ID` in GitHub.

---

## 7. Integrating Cloud Messaging

1. In Firebase Console → Project Settings → Cloud Messaging, download **server key** (or use service account).
2. Store server key as `FCM_SERVER_KEY` secret (GitHub/Render) — never commit.
3. In Cloud Functions, send messages using Admin SDK:
   ```ts
   import { initializeApp, applicationDefault } from 'firebase-admin/app';
   import { getMessaging } from 'firebase-admin/messaging';

   initializeApp({ credential: applicationDefault() });

   export const notifyConversion = onCall(async (data, context) => {
     await getMessaging().send({
       token: data.token,
       notification: {
         title: 'Conversion complete',
         body: `${data.filename} is ready to download`
       }
     });
     return { status: 'ok' };
   });
   ```
4. Client-side (Vercel frontend): request permission, retrieve FCM token, call the callable function / API.

---

## 8. Folder checklist after init

```
services/firebase/
├─ .firebaserc
├─ firebase.json
├─ firestore.indexes.json (optional)
├─ storage.rules (optional)
└─ functions/
   ├─ package.json
   ├─ tsconfig.json
   ├─ src/index.ts
   └─ lib/ (compiled JS)
```

Keep `functions/node_modules` ignored (already handled by Firebase `.gitignore`).

---

## 9. Next steps

1. Initialize project using commands above.
2. Wire REST/Callable functions for auth, billing, notifications.
3. Add tests (e.g., Jest) inside `functions/` and run in CI.
4. Configure Render/Cloud Run services to call Firebase for messaging or usage tracking.
5. Document API contracts in repo wiki or `/docs` folder.
