"""
Add $200 worth of credits to Firebase account
$200 = 15000 credits (assuming $1 = 75 credits)
"""
import os
import sys

# Use Application Default Credentials (from gcloud)
# No need to set GOOGLE_APPLICATION_CREDENTIALS

try:
    from google.cloud import firestore
    
    # Initialize Firestore
    db = firestore.Client(project='easyjpgtopdf-de346')
    
    # User details
    USER_ID = "NLhUrh6ZurQInLRV875Ktxw9rDn2"
    EMAIL = "easyjpgtopdf@gmail.com"
    CREDITS_TO_ADD = 15000  # $200 worth
    
    print(f"Adding {CREDITS_TO_ADD} credits to user {USER_ID}")
    print(f"Email: {EMAIL}")
    
    # Get user document reference
    user_ref = db.collection('users').document(USER_ID)
    
    # Get current credits
    user_doc = user_ref.get()
    
    if user_doc.exists:
        current_credits = user_doc.to_dict().get('credits', 0)
        print(f"Current credits: {current_credits}")
        
        # Update credits
        new_credits = current_credits + CREDITS_TO_ADD
        user_ref.update({
            'credits': new_credits
        })
        
        print(f"✅ Updated credits: {new_credits}")
        print(f"   Previous: {current_credits}")
        print(f"   Added: {CREDITS_TO_ADD}")
        print(f"   New total: {new_credits}")
        
    else:
        # Create new user document with credits
        user_ref.set({
            'credits': CREDITS_TO_ADD,
            'email': EMAIL,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        print(f"✅ Created new user with {CREDITS_TO_ADD} credits")
    
    # Verify
    updated_doc = user_ref.get()
    final_credits = updated_doc.to_dict().get('credits', 0)
    print(f"\n✅ VERIFICATION: Final credits = {final_credits}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

