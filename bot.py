from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from check_subscription import check_user_subscribed
from database import MongoDBClient
from scheduler import schedule_post
from keep_alive import keep_alive
import asyncio
import time

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()
keep_alive()

# ⛔ فقط ادمین‌ها اجازه آپلود دارند
@app.on_message(filters.private & filters.document)
async def handle_upload(client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply("❌ فقط ادمین‌های ربات می‌تونن فایل آپلود کنن.")
        return

    await message.reply("🎬 لطفاً اسم فیلم یا سریال رو وارد کن:")
    title = (await client.listen(message.chat.id)).text

    await message.reply("✏️ لطفاً یک کپشن کوتاه برای این فایل وارد کن:")
    caption = (await client.listen(message.chat.id)).text

    await message.reply("💡 لطفاً کیفیت این فایل رو وارد کن (مثلاً 720p):")
    quality = (await client.listen(message.chat.id)).text

    await message.reply("❓ فایل دیگه‌ای برای همین فیلم یا سریال داری؟ (بله / نه)")
    more_msg = (await client.listen(message.chat.id)).text.strip().lower()

    file_data = {
        "file_id": message.document.file_id,
        "title": title,
        "caption": caption,
        "quality": quality
    }

    db.save_file(title, file_data)

    if more_msg in ["بله", "yes"]:
        await message.reply("📤 لطفاً فایل بعدی رو برای همین فیلم آپلود کن.")
    else:
        deep_link = f"https://t.me/{BOT_USERNAME}?start={title.replace(' ', '_')}"
        await message.reply(f"✅ همه فایل‌ها ذخیره شدن.\n🔗 لینک اشتراک‌گذاری:\n{deep_link}")

# ✅ شروع - همراه با بررسی عضویت و خوش‌آمدگویی
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    args = message.text.split()
    user_id = message.from_user.id

    # اگر با لینک فیلم وارد شده
    film_key = args[1] if len(args) == 2 else None

    # بررسی عضویت در کانال‌ها
    subscribed = await check_user_subscribed(client, user_id)
    if not subscribed:
        await message.reply(
            "📢 برای استفاده از ربات ابتدا در کانال‌های زیر عضو شو:\n\n✅ بعد روی دکمه‌ی 'عضو شدم' بزن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 BoxOffice Irani", url="https://t.me/BoxOffice_Irani")],
                [InlineKeyboardButton("🎥 BoxOffice Moviiie", url="https://t.me/BoxOfficeMoviiie")],
                [InlineKeyboardButton("🎞 Animation", url="https://t.me/BoxOffice_Animation")],
                [InlineKeyboardButton("🗣 Goftegu", url="https://t.me/BoxOfficeGoftegu")],
                [InlineKeyboardButton("✅ عضو شدم", callback_data=f"checksub_{film_key or 'none'}")]
            ])
        )
        return

    # خوش‌آمدگویی فقط یک‌بار
    if not db.has_seen_welcome(user_id):
        await message.reply_photo(
            "https://i.imgur.com/HBYNljO.png",
            caption="🎉 به دنیای فیلم‌ها خوش اومدی!\n\n📥 با کلیک روی لینک هر پست، فایل‌ها رو با کیفیت‌های مختلف بگیر.",
        )
        db.mark_seen(user_id)

    if film_key:
        files = db.get_files(film_key.replace("_", " "))
        if not files:
            await message.reply("😢 متأسفم، فایلی برای این عنوان پیدا نشد.")
            return

        sent_msgs = []
        for file in files:
            caption = f"🎬 {file['title']} | کیفیت: {file['quality']}\n{file['caption']}"
            msg = await message.reply_document(file["file_id"], caption=caption)
            sent_msgs.append(msg)

        warn_msg = await message.reply("⚠️ این فایل‌ها بعد از ۳۰ ثانیه پاک می‌شن، سریع ذخیره‌شون کن!")
        await asyncio.sleep(30)
        for msg in sent_msgs + [warn_msg]:
            try:
                await msg.delete()
            except:
                pass

        db.increment_views(film_key)

# 🔁 بررسی دوباره عضویت
@app.on_callback_query(filters.regex("checksub_"))
async def recheck_subscription(client, callback):
    film_key = callback.data.split("_")[1]
    user_id = callback.from_user.id
    subscribed = await check_user_subscribed(client, user_id)

    if subscribed:
        await callback.message.delete()
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        fake_msg.text = f"/start {film_key}" if film_key != "none" else "/start"
        await start_handler(client, fake_msg)
    else:
        await callback.answer("❗️ هنوز عضو نشدی! لطفاً اول عضو شو.", show_alert=True)

idle()
