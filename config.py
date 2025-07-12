import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
ADMINS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
BOT_USERNAME = os.getenv("BOT_USERNAME")
