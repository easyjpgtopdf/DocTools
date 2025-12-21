"""
Debug script to check user credits in Firebase
Run this to diagnose credit issues
"""

import os
import sys
from firebase_credits import get_credits_from_firebase, get_credit_info_from_firebase, get_firestore_client

def check_user_credits(user_id: str):
    """Check user credits and provide detailed info."""
    print(f"\n{'='*60}")
    print(f"Checking credits for user: {user_id}")
    print(f"{'='*60}\n")
    
    # Check Firestore connection
    db = get_firestore_client()
    if not db:
        print("❌ ERROR: Firestore client not available!")
        print("   Check FIREBASE_SERVICE_ACCOUNT_JSON environment variable")
        return
    
    print("✅ Firestore client connected\n")
    
    # Get user document
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        print(f"❌ User document NOT FOUND in Firestore")
        print(f"   User ID: {user_id}")
        print(f"   Collection: users")
        print(f"   Document: {user_id}")
        print(f"\n   Possible causes:")
        print(f"   1. Wrong user_id (check Firebase UID)")
        print(f"   2. User document was deleted")
        print(f"   3. User never created in Firestore")
        return
    
    print("✅ User document found\n")
    
    # Get user data
    user_data = user_doc.to_dict()
    
    print("📊 User Credit Information:")
    print(f"   Credits: {user_data.get('credits', 'NOT SET')}")
    print(f"   Total Credits Earned: {user_data.get('totalCreditsEarned', 'NOT SET')}")
    print(f"   Total Credits Used: {user_data.get('totalCreditsUsed', 'NOT SET')}")
    print(f"   Created At: {user_data.get('createdAt', 'NOT SET')}")
    print(f"   Last Credit Update: {user_data.get('lastCreditUpdate', 'NOT SET')}")
    
    # Check credit value type
    credits = user_data.get('credits')
    print(f"\n🔍 Credit Value Analysis:")
    print(f"   Type: {type(credits)}")
    print(f"   Value: {credits}")
    
    if isinstance(credits, str):
        print(f"   ⚠️  WARNING: Credits stored as string, not number!")
        print(f"   This may cause issues. Should be int/float.")
    
    # Get via function
    print(f"\n📥 Using get_credits_from_firebase():")
    credits_from_func = get_credits_from_firebase(user_id)
    print(f"   Result: {credits_from_func}")
    
    # Get detailed info
    print(f"\n📥 Using get_credit_info_from_firebase():")
    credit_info = get_credit_info_from_firebase(user_id)
    print(f"   Result: {credit_info}")
    
    # Check recent transactions (if available)
    print(f"\n📜 Recent Activity:")
    transactions_ref = db.collection('users').document(user_id).collection('transactions')
    transactions = transactions_ref.order_by('timestamp', direction='DESCENDING').limit(10).get()
    
    if transactions:
        print(f"   Found {len(transactions)} recent transactions:")
        for txn in transactions:
            txn_data = txn.to_dict()
            print(f"   - {txn_data.get('type', 'unknown')}: {txn_data.get('amount', 0)} credits")
            print(f"     Time: {txn_data.get('timestamp', 'unknown')}")
    else:
        print(f"   No transaction history found")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_credits_debug.py <user_id>")
        print("Example: python check_credits_debug.py abc123xyz")
        sys.exit(1)
    
    user_id = sys.argv[1]
    check_user_credits(user_id)

