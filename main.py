from pyrogram import Client, idle
from config import API_ID, API_HASH, BOT_TOKEN
from keep_alive import keep_alive
from bot import register_handlers
from callbacks import register_callbacks

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

register_handlers(app)
register_callbacks(app)

if __name__ == "__main__":
    keep_alive()
    app.start()
    print("✅ Bot is running!")
    idle()
    app.stop()
