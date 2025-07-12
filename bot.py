import asyncio
import time
import threading

from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from check_subscription import check_user_subscribed
from database import MongoDBClient
from scheduler import scheduler
from keep_alive import keep_alive

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()

keep_alive()  # برای آنلاین نگه داشتن ربات روی Render
scheduler.start()  # Scheduler برای ارسال پست‌های زمان‌بندی‌شده

# فقط ادمین‌ها اجازه دارند فایل آپلود کنند
@app.on_message(filters.private & filters.document)
async def handle_upload(client, message: Message):
    if message.from_user.id not in ADMINS:
        await message.reply("❌ فقط ادمین‌ها می‌تونند فایل آپلود کنند.")
        return

    await message.reply("🎬 لطفاً نام فیلم یا سریال را وارد کنید:")
    name_msg = await client.listen(message.chat.id)
    film_name = name_msg.text.strip()

    await message.reply("📝 لطفاً یک کپشن کوتاه وارد کنید:")
    caption_msg = await client.listen(message.chat.id)
    caption = caption_msg.text.strip()

    await message.reply("🎞 کیفیت این فایل؟ (مثلاً 720p):")
    quality_msg = await client.listen(message.chat.id)
    quality = quality_msg.text.strip()

    await message.reply("📛 لطفاً یک شناسه (ID) یکتا برای این فیلم وارد کنید (مثلاً `adab`):")
    film_id_msg = await client.listen(message.chat.id)
    film_id = film_id_msg.text.strip()

    # ذخیره فایل در پایگاه داده
    db.save_file(film_id, message.document.file_id, f"{film_name} ({quality})\n\n{caption}", None)

    await message.reply("❓ فایل دیگری برای همین فیلم دارید؟ (بله/خیر)")
    more_msg = await client.listen(message.chat.id)
    if more_msg.text.lower() in ["بله", "اره", "آره", "yes", "y"]:
        await message.reply("⏫ لطفاً فایل بعدی را آپلود کنید.")
    else:
        await message.reply(
            f"✅ فایل‌ها ذخیره شدند.\n🔗 لینک به کاربر بده:\n\nhttps://t.me/{BOT_USERNAME}?start={film_id}"
        )

# کاربر هنگام کلیک روی لینک start
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    args = message.text.split()
    user_id = message.from_user.id

    # بررسی اشتراک کاربر در کانال‌ها
    subscribed = await check_user_subscribed(client, user_id)
    if not subscribed:
        buttons = [
            [InlineKeyboardButton("📣 عضویت در @BoxOffice_Irani", url="https://t.me/BoxOffice_Irani")],
            [InlineKeyboardButton("🎬 عضویت در @BoxOfficeMoviiie", url="https://t.me/BoxOfficeMoviiie")],
            [InlineKeyboardButton("📺 عضویت در @BoxOffice_Animation", url="https://t.me/BoxOffice_Animation")],
            [InlineKeyboardButton("💬 عضویت در گروه گپ", url="https://t.me/BoxOfficeGoftegu")],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="checksub_" + (args[1] if len(args) == 2 else ""))]
        ]
        await message.reply_photo(
            photo="https://i.imgur.com/HBYNljO.png",
            caption="🎉 به ربات باکس‌آفیس خوش آمدید!\n\nبرای دریافت فایل‌ها، ابتدا باید در تمام کانال‌های ما عضو شوید.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # نمایش پیام خوشامدگویی برای اولین بار
    if not db.has_seen_welcome(user_id):
        await message.reply_photo(
            "https://i.imgur.com/HBYNljO.png",
            caption="🎬 به دنیای باکس‌آفیس خوش آمدید!\nفایل‌ها رو سریع ذخیره کن چون بعد از ۳۰ ثانیه حذف می‌شن!"
        )
        db.mark_seen(user_id)

    if len(args) != 2:
        await message.reply("🤖 برای دریافت فایل‌ها، روی لینک‌های موجود در کانال کلیک کنید.")
        return

    film_id = args[1]
    files = db.get_files(film_id)
    if not files:
        await message.reply("❌ فایل مرتبطی با این شناسه پیدا نشد.")
        return

    sent = []
    for file in files:
        msg = await message.reply_document(file["file_id"], caption=file["caption"])
        sent.append(msg)

    warn = await message.reply("⚠️ فایل‌ها بعد از ۳۰ ثانیه پاک می‌شن، لطفاً ذخیره‌شون کن.")

    await asyncio.sleep(30)
    for msg in sent + [warn]:
        try:
            await msg.delete()
        except:
            pass

    db.increment_views(film_id)

# بررسی دکمه عضویت
@app.on_callback_query(filters.regex("checksub_"))
async def confirm_subscription(client, callback):
    film_id = callback.data.replace("checksub_", "")
    user_id = callback.from_user.id
    subscribed = await check_user_subscribed(client, user_id)

    if subscribed:
        await callback.message.delete()
        fake_msg = callback.message
        fake_msg.from_user = callback.from_user
        fake_msg.text = f"/start {film_id}"
        await start(client, fake_msg)
    else:
        await callback.answer("⛔️ هنوز عضو نشدی. لطفاً عضو همه کانال‌ها شو.", show_alert=True)

# اجرای همزمان Flask و Pyrogram
async def main():
    await app.start()
    print("✅ Bot is running...")
    await idle()
    await app.stop()

threading.Thread(target=lambda: asyncio.run(main())).start()
