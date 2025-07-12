import pymongo
from config import MONGO_URI, MONGO_DB

class MongoDBClient:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.files = self.db["files"]
        self.users = self.db["users"]

    # بقیه توابع بدون تغیی

    def save_file(self, film_id, file_id, caption, channel):
        self.files.insert_one({
            "film_id": film_id,
            "file_id": file_id,
            "caption": caption,
            "channel": channel,
            "views": 0
        })

    def get_files(self, film_id):
        return list(self.files.find({"film_id": film_id}))

    def increment_views(self, film_id):
        self.files.update_many({"film_id": film_id}, {"$inc": {"views": 1}})

    def has_seen_welcome(self, user_id):
        return self.users.find_one({"_id": user_id}) is not None

    def mark_seen(self, user_id):
        self.users.insert_one({"_id": user_id})
