"""
Check Firebase user data directly
"""
import os
import sys

# Set up Firebase credentials
os.environ['FIREBASE_CREDENTIALS_PATH'] = 'easyjpgtopdf-de346-firebase-adminsdk-3fwos-d68bff7bf7.json'

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # Initialize Firebase
    cred = credentials.Certificate('easyjpgtopdf-de346-firebase-adminsdk-3fwos-d68bff7bf7.json')
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    print("=" * 80)
    print("FIREBASE USER CHECK")
    print("=" * 80)
    
    # Check by UID
    user_id = "NLhUrh6ZurQInLRV875Ktxw9rDn2"
    print(f"\n1. Checking UID: {user_id}")
    user_doc = db.collection('users').document(user_id).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        print(f"   ✅ User found!")
        print(f"   Email: {user_data.get('email', 'N/A')}")
        print(f"   Credits: {user_data.get('credits', 0)}")
        print(f"   User Type: {user_data.get('userType', 'N/A')}")
        print(f"   Total Earned: {user_data.get('totalCreditsEarned', 0)}")
        print(f"   Total Used: {user_data.get('totalCreditsUsed', 0)}")
    else:
        print(f"   ❌ User NOT found with UID: {user_id}")
    
    # Check by email
    email = "easyjpgtopdf@gmail.com"
    print(f"\n2. Checking Email: {email}")
    users_query = db.collection('users').where('email', '==', email).limit(1).get()
    
    found = False
    for user in users_query:
        found = True
        user_data = user.to_dict()
        print(f"   ✅ User found!")
        print(f"   UID: {user.id}")
        print(f"   Email: {user_data.get('email', 'N/A')}")
        print(f"   Credits: {user_data.get('credits', 0)}")
        print(f"   User Type: {user_data.get('userType', 'N/A')}")
        print(f"   Total Earned: {user_data.get('totalCreditsEarned', 0)}")
        print(f"   Total Used: {user_data.get('totalCreditsUsed', 0)}")
    
    if not found:
        print(f"   ❌ User NOT found with email: {email}")
    
    # List all users with credits > 500
    print(f"\n3. Finding users with credits > 500")
    users_with_credits = db.collection('users').where('credits', '>=', 500).limit(5).get()
    
    count = 0
    for user in users_with_credits:
        count += 1
        user_data = user.to_dict()
        print(f"   User {count}:")
        print(f"     UID: {user.id}")
        print(f"     Email: {user_data.get('email', 'N/A')}")
        print(f"     Credits: {user_data.get('credits', 0)}")
    
    if count == 0:
        print(f"   ❌ No users found with credits > 500")
    
    print("\n" + "=" * 80)
    
    # Cleanup
    firebase_admin.delete_app(app)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

