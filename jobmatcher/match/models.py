from django.conf import settings
import uuid

# Access MongoDB instance
db = settings.MONGO_DB

class JobDescription:
    collection = db["job_descriptions"]

    @staticmethod
    def create(data):
        return JobDescription.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(JobDescription.collection.find({}, {"_id": 0}))


class Resume:
    collection = db["resumes"]

    @staticmethod
    def create(data):
        return Resume.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(Resume.collection.find({}, {"_id": 0}))


class Match:
    collection = db["matches"]

    @staticmethod
    def create(data):
        return Match.collection.insert_one(data)

    @staticmethod
    def get_all():
        return list(Match.collection.find({}, {"_id": 0}))
