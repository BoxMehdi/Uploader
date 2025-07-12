from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio

scheduler = AsyncIOScheduler()
scheduler.start()

def schedule_post(client, film_id, file_id, caption, schedule_time_str, channel_username):
    dt = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M")
    
    async def job():
        msg = await client.send_document(channel_username, file_id, caption=caption)
        await asyncio.sleep(30)
        await msg.delete()

    scheduler.add_job(lambda: asyncio.create_task(job()), 'date', run_date=dt)
