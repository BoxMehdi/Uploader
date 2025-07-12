from pymongo import MongoClient
import os

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[os.getenv("MONGO_DB")]
        self.files_col = self.db.files
        self.users_col = self.db.users

    def save_file(self, film_id, file_id, caption, quality, channel):
        # یک سند جدید اضافه کن برای هر فایل با کیفیتش
        self.files_col.insert_one({
            "film_id": film_id,
            "file_id": file_id,
            "caption": caption,
            "quality": quality,
            "channel": channel,
            "views": 0
        })

    def get_files(self, film_id):
        return list(self.files_col.find({"film_id": film_id}))

    def increment_views(self, film_id):
        self.files_col.update_many({"film_id": film_id}, {"$inc": {"views": 1}})

    def has_seen_welcome(self, user_id):
        user = self.users_col.find_one({"user_id": user_id})
        return user and user.get("seen_welcome", False)

    def mark_seen(self, user_id):
        self.users_col.update_one({"user_id": user_id}, {"$set": {"seen_welcome": True}}, upsert=True)
