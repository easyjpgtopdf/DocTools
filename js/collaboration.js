/**
 * Real-time Collaboration System for PDF Editor
 * Uses Firebase Firestore for real-time synchronization
 */

import { db } from './firebase-init.js';
import { auth } from './firebase-init.js';
import {
  collection,
  doc,
  setDoc,
  updateDoc,
  onSnapshot,
  serverTimestamp,
  arrayUnion,
  arrayRemove,
  query,
  where,
  orderBy,
  limit
} from 'https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js';

let currentSessionId = null;
let collaborationUnsubscribe = null;
let cursorUnsubscribe = null;
let activeUsers = new Map();
let currentUser = null;

/**
 * Initialize collaboration session
 */
export async function initCollaboration(pdfFileId) {
  try {
    currentUser = auth.currentUser;
    if (!currentUser) {
      console.warn('User not authenticated, collaboration disabled');
      return false;
    }

    // Create or join collaboration session
    currentSessionId = `pdf_${pdfFileId}`;
    const sessionRef = doc(db, 'collaboration_sessions', currentSessionId);

    // Add current user to active users
    await updateDoc(sessionRef, {
      activeUsers: arrayUnion({
        userId: currentUser.uid,
        displayName: currentUser.displayName || currentUser.email,
        email: currentUser.email,
        joinedAt: serverTimestamp(),
        lastSeen: serverTimestamp()
      }),
      lastActivity: serverTimestamp()
    }, { merge: true });

    // Listen for real-time updates
    setupRealtimeListeners(sessionRef);

    // Set up cursor tracking
    setupCursorTracking(sessionRef);

    // Set up presence (heartbeat)
    setupPresence(sessionRef);

    console.log('✅ Collaboration initialized for session:', currentSessionId);
    return true;
  } catch (error) {
    console.error('Error initializing collaboration:', error);
    return false;
  }
}

/**
 * Set up real-time listeners for PDF edits
 */
function setupRealtimeListeners(sessionRef) {
  // Listen for PDF edits
  const editsRef = collection(db, 'collaboration_sessions', currentSessionId, 'edits');
  const editsQuery = query(editsRef, orderBy('timestamp', 'desc'), limit(50));

  collaborationUnsubscribe = onSnapshot(editsQuery, (snapshot) => {
    snapshot.docChanges().forEach((change) => {
      if (change.type === 'added' || change.type === 'modified') {
        const edit = change.doc.data();
        if (edit.userId !== currentUser.uid) {
          // Apply remote edit
          applyRemoteEdit(edit);
        }
      }
    });
  }, (error) => {
    console.error('Collaboration listener error:', error);
  });
}

/**
 * Set up cursor tracking
 */
function setupCursorTracking(sessionRef) {
  const cursorsRef = collection(db, 'collaboration_sessions', currentSessionId, 'cursors');

  cursorUnsubscribe = onSnapshot(cursorsRef, (snapshot) => {
    snapshot.docChanges().forEach((change) => {
      const cursorData = change.doc.data();
      const userId = change.doc.id;

      if (change.type === 'added' || change.type === 'modified') {
        if (userId !== currentUser.uid) {
          updateRemoteCursor(userId, cursorData);
        }
      } else if (change.type === 'removed') {
        removeRemoteCursor(userId);
      }
    });
  });
}

/**
 * Set up presence (heartbeat to show user is active)
 */
function setupPresence(sessionRef) {
  // Update last seen every 10 seconds
  const presenceInterval = setInterval(async () => {
    if (currentUser && currentSessionId) {
      try {
        await updateDoc(sessionRef, {
          [`activeUsers.${currentUser.uid}.lastSeen`]: serverTimestamp()
        }, { merge: true });
      } catch (error) {
        console.error('Presence update error:', error);
      }
    }
  }, 10000);

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    clearInterval(presenceInterval);
    leaveCollaboration();
  });
}

/**
 * Broadcast PDF edit to other users
 */
export async function broadcastEdit(editData) {
  if (!currentSessionId || !currentUser) return;

  try {
    const editsRef = collection(db, 'collaboration_sessions', currentSessionId, 'edits');
    const editDoc = doc(editsRef);

    await setDoc(editDoc, {
      userId: currentUser.uid,
      displayName: currentUser.displayName || currentUser.email,
      type: editData.type, // 'text', 'image', 'annotation', etc.
      data: editData.data,
      timestamp: serverTimestamp(),
      pageIndex: editData.pageIndex || 0
    });

    // Update session last activity
    const sessionRef = doc(db, 'collaboration_sessions', currentSessionId);
    await updateDoc(sessionRef, {
      lastActivity: serverTimestamp()
    });
  } catch (error) {
    console.error('Error broadcasting edit:', error);
  }
}

/**
 * Broadcast cursor position
 */
export async function broadcastCursor(x, y, pageIndex) {
  if (!currentSessionId || !currentUser) return;

  try {
    const cursorsRef = collection(db, 'collaboration_sessions', currentSessionId, 'cursors');
    const cursorDoc = doc(cursorsRef, currentUser.uid);

    await setDoc(cursorDoc, {
      userId: currentUser.uid,
      displayName: currentUser.displayName || currentUser.email,
      x: x,
      y: y,
      pageIndex: pageIndex,
      timestamp: serverTimestamp()
    }, { merge: true });
  } catch (error) {
    console.error('Error broadcasting cursor:', error);
  }
}

/**
 * Apply remote edit to PDF
 */
function applyRemoteEdit(edit) {
  // Dispatch custom event for PDF editor to handle
  document.dispatchEvent(new CustomEvent('remote-edit', {
    detail: edit
  }));
}

/**
 * Update remote user cursor
 */
function updateRemoteCursor(userId, cursorData) {
  activeUsers.set(userId, cursorData);
  
  // Dispatch event to show cursor
  document.dispatchEvent(new CustomEvent('remote-cursor', {
    detail: { userId, ...cursorData }
  }));
}

/**
 * Remove remote user cursor
 */
function removeRemoteCursor(userId) {
  activeUsers.delete(userId);
  
  // Dispatch event to hide cursor
  document.dispatchEvent(new CustomEvent('remote-cursor-removed', {
    detail: { userId }
  }));
}

/**
 * Get active users in session
 */
export function getActiveUsers() {
  return Array.from(activeUsers.values());
}

/**
 * Leave collaboration session
 */
export async function leaveCollaboration() {
  if (!currentSessionId || !currentUser) return;

  try {
    const sessionRef = doc(db, 'collaboration_sessions', currentSessionId);
    
    // Remove user from active users
    await updateDoc(sessionRef, {
      activeUsers: arrayRemove({
        userId: currentUser.uid
      })
    });

    // Remove cursor
    const cursorsRef = collection(db, 'collaboration_sessions', currentSessionId, 'cursors');
    const cursorDoc = doc(cursorsRef, currentUser.uid);
    await setDoc(cursorDoc, {
      userId: currentUser.uid,
      active: false
    });

    // Unsubscribe from listeners
    if (collaborationUnsubscribe) {
      collaborationUnsubscribe();
      collaborationUnsubscribe = null;
    }
    if (cursorUnsubscribe) {
      cursorUnsubscribe();
      cursorUnsubscribe = null;
    }

    currentSessionId = null;
    activeUsers.clear();
    console.log('✅ Left collaboration session');
  } catch (error) {
    console.error('Error leaving collaboration:', error);
  }
}

/**
 * Share PDF with other users
 */
export async function sharePDF(email, permission = 'edit') {
  if (!currentSessionId || !currentUser) return false;

  try {
    const sharesRef = collection(db, 'collaboration_sessions', currentSessionId, 'shares');
    const shareDoc = doc(sharesRef);

    await setDoc(shareDoc, {
      email: email,
      permission: permission, // 'view' or 'edit'
      sharedBy: currentUser.uid,
      sharedAt: serverTimestamp()
    });

    return true;
  } catch (error) {
    console.error('Error sharing PDF:', error);
    return false;
  }
}

// Export for use in other files
window.collaborationService = {
  initCollaboration,
  broadcastEdit,
  broadcastCursor,
  getActiveUsers,
  leaveCollaboration,
  sharePDF
};





