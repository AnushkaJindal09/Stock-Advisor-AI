"""# backend/scheduler/task_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
import time

def scheduled_task():
    print("Updating stock data...")  # Replace with your logic

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', minutes=5)
    scheduler.start()
    print("Scheduler started.")
"""

from apscheduler.schedulers.background import BackgroundScheduler
from update_data_only import update_data_only

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        update_data_only,
        'cron',
        hour=18,
        minute=30   # market close
    )
    scheduler.start()
    print("✅ Scheduler started")
