"""
Direct Firebase Credit Check for UID: NLhUrh6ZurQInLRV875Ktxw9rDn2
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pdf-to-excel-backend'))

# Import credit module
from firebase_credits import get_credits_from_firebase, get_firestore_client
from google.cloud import firestore

def check_user_credits():
    """Check actual credits in Firebase"""
    user_id = "NLhUrh6ZurQInLRV875Ktxw9rDn2"
    
    print("=" * 80)
    print("FIREBASE CREDIT CHECK")
    print("=" * 80)
    print(f"\nUser ID: {user_id}")
    print(f"Email: easyjpgtopdf@gmail.com")
    
    # Get Firestore client
    db = get_firestore_client()
    if not db:
        print("\n❌ ERROR: Firestore client not available")
        return
    
    # Get user document
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        print(f"\n❌ ERROR: User document NOT FOUND in Firestore!")
        print("   This means the UID is incorrect or user doesn't exist.")
        return
    
    user_data = user_doc.to_dict()
    
    print(f"\n✅ User found!")
    print(f"\n📊 CREDIT DETAILS:")
    print(f"   Current Credits: {user_data.get('credits', 'N/A')}")
    print(f"   Total Earned: {user_data.get('totalCreditsEarned', 'N/A')}")
    print(f"   Total Used: {user_data.get('totalCreditsUsed', 'N/A')}")
    print(f"   User Type: {user_data.get('userType', 'N/A')}")
    print(f"   Email: {user_data.get('email', 'N/A')}")
    
    # Check if credits field exists
    if 'credits' not in user_data:
        print(f"\n⚠️  WARNING: 'credits' field is MISSING from user document!")
        print("   This will cause 0 credits to be returned.")
    elif user_data.get('credits') is None:
        print(f"\n⚠️  WARNING: 'credits' field is NULL!")
    elif user_data.get('credits') == 0:
        print(f"\n⚠️  WARNING: User has 0 credits!")
        print("   Expected: 508 credits")
        print("   This is a DATA LOSS issue - credits disappeared!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        check_user_credits()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

