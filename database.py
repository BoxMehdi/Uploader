from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.files = self.db.files
        self.users = self.db.users

    def save_file(self, film_id, file_id, caption, quality):
        self.files.insert_one({
            "film_id": film_id,
            "file_id": file_id,
            "caption": caption,
            "quality": quality
        })

    def get_files(self, film_id):
        return list(self.files.find({"film_id": film_id}))

    def has_seen_welcome(self, user_id):
        return self.users.find_one({"user_id": user_id}) is not None

    def mark_seen(self, user_id):
        self.users.insert_one({"user_id": user_id})

    def increment_views(self, film_id):
        self.db.stats.update_one({"film_id": film_id}, {"$inc": {"views": 1}}, upsert=True)
