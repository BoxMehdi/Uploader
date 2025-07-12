from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from check_subscription import check_user_subscribed
from database import MongoDBClient
from scheduler import schedule_post
from keep_alive import keep_alive
import asyncio

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()
keep_alive()

@app.on_message(filters.private & filters.document)
async def handle_upload(client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply("❌ فقط ادمین‌ها می‌تونن فایل آپلود کنن.")
        return

    await message.reply("🎬 اسم فیلم یا سریال؟")
    title = (await client.listen(message.chat.id)).text

    await message.reply("📝 کپشن؟")
    caption = (await client.listen(message.chat.id)).text

    await message.reply("💡 کیفیت؟ (مثلاً 720p)")
    quality = (await client.listen(message.chat.id)).text

    file_data = {
        "file_id": message.document.file_id,
        "title": title,
        "caption": caption,
        "quality": quality
    }

    db.save_file(title, file_data)

    deep_link = f"https://t.me/{BOT_USERNAME}?start={title.replace(' ', '_')}"
    await message.reply(f"✅ فایل ذخیره شد.\n🔗 لینک:\n{deep_link}")

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    film_key = args[1] if len(args) > 1 else None

    if not await check_user_subscribed(client, user_id):
        await message.reply(
            "📢 لطفاً اول عضو کانال‌ها شو:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 BoxOffice Irani", url=JOIN_LINK_2)],
                [InlineKeyboardButton("🎥 BoxOffice Moviiie", url=JOIN_LINK_1)],
                [InlineKeyboardButton("🎞 Animation", url=JOIN_LINK_3)],
                [InlineKeyboardButton("🗣 Goftegu", url=JOIN_LINK_4)],
                [InlineKeyboardButton("✅ عضو شدم", callback_data=f"checksub_{film_key or 'none'}")]
            ])
        )
        return

    if not db.has_seen_welcome(user_id):
        await message.reply_photo(WELCOME_IMAGE, caption=WELCOME_TEXT)
        db.mark_seen(user_id)

    if film_key:
        files = db.get_files(film_key.replace("_", " "))
        if not files:
            await message.reply("😔 فایلی پیدا نشد.")
            return

        sent = []
        for file in files:
            cap = f"🎬 {file['title']} | کیفیت: {file['quality']}\n{file['caption']}"
            msg = await message.reply_document(file["file_id"], caption=cap)
            sent.append(msg)

        warn = await message.reply("⚠️ این فایل‌ها بعد از 30 ثانیه حذف می‌شن. ذخیره کن!")
        await asyncio.sleep(30)
        for m in sent + [warn]:
            try: await m.delete()
            except: pass

        db.increment_views(film_key)

@app.on_callback_query(filters.regex("checksub_"))
async def recheck_subscription(client, callback):
    film_key = callback.data.split("_")[1]
    if await check_user_subscribed(client, callback.from_user.id):
        await callback.message.delete()
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        fake_msg.text = f"/start {film_key}" if film_key != "none" else "/start"
        await start_handler(client, fake_msg)
    else:
        await callback.answer("❗️ هنوز عضو نشدی!", show_alert=True)

idle()
