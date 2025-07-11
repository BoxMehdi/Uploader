from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.files_col = self.db["files"]
        self.stats_col = self.db["stats"]

    def save_file(self, film_id, file_id, quality, caption):
        if self.files_col.find_one({"film_id": film_id,"file_id": file_id}):
            return False
        self.files_col.insert_one({
            "film_id": film_id,
            "file_id": file_id,
            "quality": quality,
            "caption": caption
        })
        self.stats_col.update_one(
            {"film_id": film_id},
            {"$setOnInsert":{"views":0,"downloads":0,"shares":0}},
            upsert=True
        )
        return True

    def get_files(self, film_id):
        return list(self.files_col.find({"film_id": film_id}))

    def increment(self, film_id, stat_type):
        if stat_type in ["views","downloads","shares"]:
            self.stats_col.update_one({"film_id":film_id}, {"$inc":{stat_type:1}})

    def get_stats(self, film_id):
        s = self.stats_col.find_one({"film_id":film_id})
        return {"views": s.get("views",0), "downloads": s.get("downloads",0), "shares": s.get("shares",0)} if s else {"views":0,"downloads":0,"shares":0}
