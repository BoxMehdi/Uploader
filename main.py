import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import bot, callbacks  # imports handlers

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = Client("BoxOfficeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    app.include(bot.app)
    app.include(callbacks.app)
    app.run()
