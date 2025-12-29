"""Find Firebase user ID by email"""
from firebase_credits import db

email = 'easyjpgtopdf@gmail.com'
users = db.collection('users').where('email', '==', email).limit(1).get()

for user in users:
    user_data = user.to_dict()
    print(f"User ID: {user.id}")
    print(f"Email: {user_data.get('email')}")
    print(f"Credits: {user_data.get('credits', 0)}")
    print(f"User Type: {user_data.get('userType', 'N/A')}")
    print(f"Total Credits Earned: {user_data.get('totalCreditsEarned', 0)}")
    print(f"Total Credits Used: {user_data.get('totalCreditsUsed', 0)}")
    break
else:
    print(f"No user found with email: {email}")

