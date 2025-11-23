import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js";
import { getMessaging, isSupported } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js";

// Firebase configuration - Client-side Web SDK
// Note: API keys are safe to expose as they're client-side keys
// They only allow access to specific Firebase resources configured in Firebase Console
export const firebaseConfig = {
  apiKey: "AIzaSyBch3tJoeFqio3IA4MbPoh2GHZE2qKVzGc",
  authDomain: "easyjpgtopdf-de346.firebaseapp.com",
  projectId: "easyjpgtopdf-de346",
  storageBucket: "easyjpgtopdf-de346.appspot.com",
  messagingSenderId: "564572183797",
  appId: "1:564572183797:web:9c204df018c150f02f79bc"
};

export const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

async function initMessaging() {
  if (!(await isSupported())) {
    console.warn("Firebase Messaging not supported in this browser.");
    return null;
  }

  try {
    const messaging = getMessaging(app);
    
    // Request notification permission
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      console.log('Notification permission granted');
      
      // Get FCM token
      try {
        const token = await messaging.getToken({
          vapidKey: 'YOUR_VAPID_KEY_HERE' // Replace with your VAPID key from Firebase Console
        });
        if (token) {
          console.log('FCM Token:', token);
          // You can send this token to your server to store it
        }
      } catch (tokenError) {
        console.warn('Failed to get FCM token:', tokenError);
      }
    } else {
      console.warn('Notification permission denied');
    }
    
    return messaging;
  } catch (error) {
    console.error("Failed to initialize Firebase Messaging", error);
    return null;
  }
}

// Initialize messaging when service worker is ready
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.ready.then(() => {
    initMessaging().catch((error) => {
      console.error("Failed to initialise Firebase Messaging", error);
    });
  });
} else {
  console.warn("Service Workers not supported in this browser.");
}
