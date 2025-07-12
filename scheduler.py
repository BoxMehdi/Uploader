from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def schedule_post(app, film_id, file_id, caption, post_time, channel_username):
    async def post_file():
        await app.send_document(chat_id=channel_username, document=file_id, caption=caption)
    scheduler.add_job(post_file, "date", run_date=post_time)
