import asyncio
import time
import threading
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from config import *
from database import MongoDBClient
from scheduler import schedule_post, scheduler
from keep_alive import keep_alive
from check_subscription import check_user_subscribed
from utils import subscription_keyboard

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoDBClient()
keep_alive()

@app.on_message(filters.private & filters.user(ADMIN_IDS) & filters.document)
async def upload_file(client, message: Message):
    await message.reply("🎬 اسم فیلم/سریال:")
    film_name = (await client.listen(message.chat.id)).text

    await message.reply("✏️ کپشن کوتاه:")
    caption = (await client.listen(message.chat.id)).text

    await message.reply("💠 کیفیت فایل (مثلاً 720p):")
    quality = (await client.listen(message.chat.id)).text

    await message.reply("📥 فایل دیگر برای این فیلم داری؟ (بله/خیر)")
    more = (await client.listen(message.chat.id)).text.lower()

    db.save_file(film_name, message.document.file_id, f"{caption}\n📥 کیفیت: {quality}", quality)

    if "خیر" in more:
        await message.reply(f"✅ ذخیره شد.\n🔗 لینک اشتراک‌گذاری: https://t.me/{BOT_USERNAME}?start={film_name}")

@app.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    args = message.text.split()
    user_id = message.from_user.id

    if len(args) == 2:
        film_id = args[1]

        if not await check_user_subscribed(client, user_id):
            await message.reply("📣 لطفاً ابتدا در کانال‌های زیر عضو شوید:", reply_markup=subscription_keyboard())
            return

        if not db.has_seen_welcome(user_id):
            await message.reply_photo("https://i.imgur.com/HBYNljO.png", caption="🎉 به دنیای فیلم خوش اومدی!\n👇 ابتدا از کانال‌ها عضو شو!")
            db.mark_seen(user_id)

        files = db.get_files(film_id)
        sent = []
        for f in files:
            msg = await message.reply_document(f['file_id'], caption=f['caption'])
            sent.append(msg)

        warn = await message.reply("⚠️ این فایل‌ها تا ۳۰ ثانیه دیگه حذف می‌شن، ذخیره کن!")
        await asyncio.sleep(30)
        for msg in sent + [warn]:
            await msg.delete()

        db.increment_views(film_id)

@app.on_callback_query(filters.regex("checksub"))
async def on_sub_check(client, callback):
    user_id = callback.from_user.id
    if await check_user_subscribed(client, user_id):
        await callback.message.delete()
        await callback.message.reply("✅ عضویت شما تأیید شد. لطفاً دوباره دستور /start را بزنید.")
    else:
        await callback.answer("🚫 هنوز عضو نشدی!", show_alert=True)

async def main():
    scheduler.start()
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
