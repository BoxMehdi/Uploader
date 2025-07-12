from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from check_subscription import check_user_subscribed
from database import MongoDBClient
from scheduler import schedule_post
from keep_alive import keep_alive
import asyncio
import time
import threading

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()

# اجرای Flask روی ترد جداگانه برای UptimeRobot
threading.Thread(target=keep_alive).start()

@app.on_message(filters.private & filters.user(ADMINS) & filters.document)
async def upload_file(client, message: Message):
    file_id = message.document.file_id
    await message.reply("🔢 لطفاً شناسه فیلم (filmID) را وارد کنید:")
    film_id_msg = await client.listen(message.chat.id)
    film_id = film_id_msg.text.strip()

    await message.reply("📝 لطفاً کپشن فیلم را وارد کنید:")
    caption_msg = await client.listen(message.chat.id)
    caption = caption_msg.text.strip()

    await message.reply("🕰 زمان ارسال را وارد کنید (مثلاً 2025-07-11 18:00):")
    time_msg = await client.listen(message.chat.id)
    schedule_time = time_msg.text.strip()

    await message.reply("🎯 کانال مقصد را وارد کنید (مثلاً @BoxOffice_Irani):")
    channel_msg = await client.listen(message.chat.id)
    channel_username = channel_msg.text.strip()

    db.save_file(film_id, file_id, caption, channel_username)
    schedule_post(app, film_id, file_id, caption, schedule_time, channel_username)

    await message.reply(
        f"✅ ذخیره شد و در زمان تعیین‌شده پست خواهد شد.\n"
        f"🔗 لینک: https://t.me/{BOT_USERNAME}?start={film_id}"
    )

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    args = message.text.split(" ")
    if len(args) == 2:
        film_id = args[1]
        user_id = message.from_user.id

        subscribed = await check_user_subscribed(client, user_id)
        if not subscribed:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📣 عضویت در کانال‌ها", url="https://t.me/BoxOfficeMoviiie")],
                [InlineKeyboardButton("✅ عضو شدم", callback_data=f"checksub_{film_id}")]
            ])
            await message.reply("📢 لطفاً اول در کانال‌های ما عضو شوید:", reply_markup=markup)
            return

        if not db.has_seen_welcome(user_id):
            await message.reply_photo(
                "https://example.com/welcome.jpg",
                caption="🎬 به ربات خوش آمدید!"
            )
            db.mark_seen(user_id)

        files = db.get_files(film_id)
        sent = []
        for file in files:
            msg = await message.reply_document(file['file_id'], caption=file['caption'])
            sent.append(msg)

        warn = await message.reply("⚠️ این فایل‌ها بعد از ۳۰ ثانیه پاک می‌شن، حتماً ذخیره کنید.")
        await asyncio.sleep(30)
        for msg in sent + [warn]:
            await msg.delete()

        db.increment_views(film_id)

@app.on_callback_query(filters.regex("checksub_"))
async def checksub(client, callback):
    film_id = callback.data.split("_")[1]
    subscribed = await check_user_subscribed(client, callback.from_user.id)
    if subscribed:
        await callback.message.delete()
        await start(client, callback.message)
    else:
        await callback.answer("هنوز عضو نشدی!", show_alert=True)

app.run()
