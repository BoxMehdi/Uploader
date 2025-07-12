bot.run()
import asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_IDS
from database import MongoDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = MongoDBClient()
app = Client("BoxOfficeBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

upload_sessions = {}

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply("سلام! ربات آنلاین و آماده‌ست 😊\nبرای آپلود فایل /upload را بزنید.")

@app.on_message(filters.command("upload") & filters.private & filters.user(ADMIN_IDS))
async def start_upload(c, m):
    upload_sessions[m.from_user.id] = {"film_id": None, "files": [], "phase": "awaiting_id"}
    await m.reply("📌 شناسه (Film ID) فیلم را ارسال کن:")

@app.on_message(filters.private & filters.media & filters.user(ADMIN_IDS))
async def handle_media(c, m):
    uid = m.from_user.id
    sess = upload_sessions.get(uid)
    if not sess or sess["phase"] != "awaiting_file":
        return
    fid = m.video.file_id if m.video else m.document.file_id
    sess["files"].append({"file_id": fid, "quality": None, "caption": None})
    sess["phase"] = "awaiting_quality"
    await m.reply("کیفیت فایل؟ (مثلاً 720p)")

@app.on_message(filters.private & filters.text & filters.user(ADMIN_IDS))
async def handle_text(c, m):
    uid = m.from_user.id
    sess = upload_sessions.get(uid)
    if not sess: return

    txt = m.text.strip()
    phase = sess["phase"]

    if phase == "awaiting_id":
        sess["film_id"] = txt
        sess["phase"] = "awaiting_file"
        await m.reply("📁 فایل فیلم را ارسال کن:")

    elif phase == "awaiting_quality":
        sess["files"][-1]["quality"] = txt
        sess["phase"] = "awaiting_caption"
        await m.reply("📝 کپشن فایل؟")

    elif phase == "awaiting_caption":
        sess["files"][-1]["caption"] = txt
        sess["phase"] = "ask_more"
        await m.reply("📌 آیا فایل دیگه برای این فیلم هست؟ (بله/خیر)")

    elif phase == "ask_more":
        if txt.lower() in ["بله","yes","آره","اره"]:
            sess["phase"] = "awaiting_file"
            await m.reply("📁 فایل بعدی رو بفرست:")
        elif txt.lower() in ["خیر","no","نه"]:
            count = 0
            for f in sess["files"]:
                if db.save_file(sess["film_id"], f["file_id"], f["quality"], f["caption"]):
                    count += 1
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("دریافت🎬", callback_data=f"get:{sess['film_id']}")
            ]])
            await m.reply(f"✅ {count} فایل ذخیره شد.", reply_markup=kb)
            upload_sessions.pop(uid, None)
        else:
            await m.reply("❗ فقط «بله» یا «خیر» بنویس.")
