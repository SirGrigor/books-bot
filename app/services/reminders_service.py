from apscheduler.schedulers.background import BackgroundScheduler
from app.database.db_handler import DBHandler

class RemindersService:
    def __init__(self, db_handler):
        """
        Initializes the RemindersService with a database handler.
        """
        self.scheduler = BackgroundScheduler()
        self.db_handler = db_handler

    def schedule_reminder(self, user_id, message, delay):
        """
        Schedules a reminder and saves it to the database.
        """
        job = self.scheduler.add_job(
            self.send_reminder,
            'interval',
            days=delay,
            args=[user_id, message]
        )

        # Save the reminder to the database
        self.db_handler.save_reminder(user_id=user_id, message=message, delay=delay, job_id=job.id)

    def send_reminder(self, user_id, message):
        """
        Sends a reminder message to the user.
        """
        print(f"Reminder for user {user_id}: {message}")

    def start(self):
        """
        Starts the scheduler.
        """
        self.scheduler.start()