from django.conf import settings
import uuid

db = settings.MONGO_DB  # Ensure MONGO_DB is properly configured in settings.py

class UserProfile:
    collection = db["users"]

    @staticmethod
    def create(data):
        return UserProfile.collection.insert_one(data)

    @staticmethod
    def get_by_email(email):
        return UserProfile.collection.find_one({"email": email})

    @staticmethod
    def get_by_id(user_id):
        return UserProfile.collection.find_one({"_id": user_id})
