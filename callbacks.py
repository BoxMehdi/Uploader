from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from database import MongoDBClient
from config import ADMIN_IDS

db = MongoDBClient()

@Client.on_callback_query(filters.regex(r"^get:(.+)"))
async def serve_files(c: Client, cq: CallbackQuery):
    fid = cq.data.split(":",1)[1]
    files = db.get_files(fid)
    if not files:
        return await cq.answer("❌ فایلی برای این آی‌دی نیست.")
    for f in files:
        db.increment(fid, "downloads")
        await c.send_cached_media(cq.message.chat.id, f["file_id"], caption=f"*{fid}* — {f['quality']}\n{f['caption']}", parse_mode="markdown")
    stats = db.get_stats(fid)
    await cq.message.edit(f"✅ تمام فایل‌ها ارسال شد!\n📊 ویو: {stats['views']} | دانلود: {stats['downloads']}")
    await cq.answer()
