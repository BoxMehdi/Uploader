from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Berlin"))
scheduler.start()

def schedule_post(app, film_id, file_id, caption, time_str, channel_username):
    def job():
        app.send_document(channel_username, file_id, caption=caption)

    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    scheduler.add_job(job, "date", run_date=dt)
