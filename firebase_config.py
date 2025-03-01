import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_user_ref(user_id):
    """Returns Firestore reference for a user."""
    return db.collection("users").document(user_id)
