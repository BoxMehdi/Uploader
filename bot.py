import os
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import MongoDBClient
from check_subscription import check_user_subscribed
from scheduler import schedule_post
from keep_alive import keep_alive
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
BOT_USERNAME = os.getenv("BOT_USERNAME")
WELCOME_IMG = os.getenv("WELCOME_IMG")

CHANNEL_LINKS = os.getenv("CHANNEL_LINKS").split(",")

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()
keep_alive()

# --- آپلود فایل فقط برای ادمین‌ها ---
@app.on_message(filters.private & filters.user(ADMINS) & filters.document)
async def upload_file(client, message: Message):
    await message.reply("🔢 لطفاً شناسه فیلم (filmID) را وارد کنید:")
    film_id_msg = await app.listen(message.chat.id)
    film_id = film_id_msg.text.strip()

    await message.reply("📝 لطفاً کپشن کوتاه فیلم را وارد کنید:")
    caption_msg = await app.listen(message.chat.id)
    caption = caption_msg.text.strip()

    await message.reply("🎞 لطفاً کیفیت فیلم را وارد کنید (مثلاً 360p, 480p, 720p):")
    quality_msg = await app.listen(message.chat.id)
    quality = quality_msg.text.strip()

    await message.reply("🕰 لطفاً زمان ارسال را به شکل YYYY-MM-DD HH:MM وارد کنید:")
    time_msg = await app.listen(message.chat.id)
    schedule_time = time_msg.text.strip()

    await message.reply("🎯 لطفاً نام کانال مقصد را وارد کنید (مثلاً @BoxOffice_Irani):")
    channel_msg = await app.listen(message.chat.id)
    channel_username = channel_msg.text.strip()

    file_id = message.document.file_id
    db.save_file(film_id, file_id, caption, quality, channel_username)
    schedule_post(app, film_id, file_id, caption, schedule_time, channel_username)

    await message.reply(f"✅ فایل ذخیره شد و در زمان تعیین شده ارسال خواهد شد.\n🔗 لینک برای کاربران:\nhttps://t.me/{BOT_USERNAME}?start={film_id}")

# --- استارت و بررسی عضویت ---
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    args = message.text.split()
    user_id = message.from_user.id

    # بررسی عضویت
    if not await check_user_subscribed(client, user_id):
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"1️⃣ عضویت در کانال BoxOffice Irani", url=CHANNEL_LINKS[0])],
            [InlineKeyboardButton(f"2️⃣ عضویت در کانال BoxOffice Moviiie", url=CHANNEL_LINKS[1])],
            [InlineKeyboardButton(f"3️⃣ عضویت در کانال BoxOffice Animation", url=CHANNEL_LINKS[2])],
            [InlineKeyboardButton(f"4️⃣ عضویت در کانال BoxOffice GAP", url=CHANNEL_LINKS[3])],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="checksubs")]
        ])
        await message.reply("📢 لطفاً ابتدا در کانال‌های زیر عضو شوید:", reply_markup=markup)
        return

    # پیام خوش آمدگویی فقط یکبار
    if not db.has_seen_welcome(user_id):
        await message.reply_photo(WELCOME_IMG, caption="🎬 به ربات باکس‌آفیس خوش آمدید! برای دریافت فیلم‌ها از لینک‌ها استفاده کنید.")
        db.mark_seen(user_id)

    # اگر کاربر با استارت لینک (مثلا start=film_id) آمده باشد
    if len(args) == 2:
        film_id = args[1]
        files = db.get_files(film_id)
        if not files:
            await message.reply("⚠️ فیلم یا سریالی با این شناسه یافت نشد.")
            return

        sent_messages = []
        for file in files:
            # کپشن رو به صورت ترکیبی از کیفیت و متن بفرست
            caption = f"🎞 کیفیت: {file['quality']}\n\n{file['caption']}"
            msg = await message.reply_document(file['file_id'], caption=caption)
            sent_messages.append(msg)

        # پیام هشدار حذف ۳۰ ثانیه‌ای
        warn_msg = await message.reply("⚠️ این فایل‌ها پس از ۳۰ ثانیه حذف خواهند شد، لطفاً ذخیره کنید!")
        sent_messages.append(warn_msg)

        await asyncio.sleep(30)

        for msg in sent_messages:
            try:
                await msg.delete()
            except:
                pass

        db.increment_views(film_id)

    else:
        # اگر فقط /start بدون آرگومان بود، پیام راهنما بفرست
        await message.reply("سلام! برای دریافت فیلم‌ها لینک مخصوص رو از کانال‌ها دریافت و استارت کنید.")

# --- دکمه تأیید عضویت ---
@app.on_callback_query(filters.regex("checksubs"))
async def check_subs_callback(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_user_subscribed(client, user_id):
        await callback.message.delete()
        await callback.answer("✅ عضویت شما تایید شد!")
        await start_cmd(client, callback.message)
    else:
        await callback.answer("❌ هنوز عضو همه کانال‌ها نیستید!", show_alert=True)

# --- حذف پیام‌های اضافی و کنترل خطا ---
@app.on_message(filters.private & ~filters.user(ADMINS) & filters.document)
async def unauthorized_upload(client, message: Message):
    await message.reply("❌ فقط ادمین‌ها اجازه آپلود دارند.")

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
