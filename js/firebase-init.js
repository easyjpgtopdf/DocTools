import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js";
import { getMessaging, isSupported } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging.js";

// Firebase configuration - can be loaded from environment variables or hardcoded
// In production, this comes from environment variables set in Vercel/Heroku dashboard
export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyBch3tJoeFqio3IA4MbPoh2GHZE2qKVzGc",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "easyjpgtopdf-de346.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "easyjpgtopdf-de346",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "easyjpgtopdf-de346.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "564572183797",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:564572183797:web:9c204df018c150f02f79bc"
};

export const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

async function initMessaging() {
  if (!(await isSupported())) {
    console.warn("Firebase Messaging not supported in this browser.");
    return null;
  }

  const messaging = getMessaging(app);
  return messaging;
}

initMessaging().catch((error) => {
  console.error("Failed to initialise Firebase Messaging", error);
});
