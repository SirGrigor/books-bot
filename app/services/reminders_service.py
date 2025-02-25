from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from constants.constants import TELEGRAM_BOT_TOKEN

scheduler = BackgroundScheduler()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def schedule_reminder(chat_id, summary, intervals=[1, 3, 7, 30]):
    """
    Schedules spaced repetition reminders.
    """
    for interval in intervals:
        scheduler.add_job(send_reminder, 'interval', days=interval, args=[chat_id, summary])

def send_reminder(chat_id, summary):
    """
    Sends a reminder message via Telegram.
    """
    bot.send_message(chat_id=chat_id, text=f"Reminder: {summary}")

# Start the scheduler
scheduler.start()