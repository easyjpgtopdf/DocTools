// Firebase Cloud Messaging Service Worker
// This file must be in the root directory for Firebase Messaging to work

importScripts('https://www.gstatic.com/firebasejs/10.14.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging-compat.js');

// Firebase configuration (same as in firebase-init.js)
const firebaseConfig = {
  apiKey: "AIzaSyBch3tJoeFqio3IA4MbPoh2GHZE2qKVzGc",
  authDomain: "easyjpgtopdf-de346.firebaseapp.com",
  projectId: "easyjpgtopdf-de346",
  storageBucket: "easyjpgtopdf-de346.appspot.com",
  messagingSenderId: "564572183797",
  appId: "1:564572183797:web:9c204df018c150f02f79bc"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Retrieve an instance of Firebase Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  
  const notificationTitle = payload.notification?.title || 'easyjpgtopdf';
  const notificationOptions = {
    body: payload.notification?.body || 'You have a new notification',
    icon: payload.notification?.icon || '/images/logo.png',
    badge: '/images/logo.png',
    tag: payload.data?.tag || 'default',
    data: payload.data || {}
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[firebase-messaging-sw.js] Notification click received.');
  
  event.notification.close();

  // Get the URL from notification data or use default
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      // Check if there's already a window/tab open with the target URL
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      // If no window is open, open a new one
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

