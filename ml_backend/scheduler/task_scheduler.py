# backend/scheduler/task_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
import time

def scheduled_task():
    print("Updating stock data...")  # Replace with your logic

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', minutes=5)
    scheduler.start()
    print("Scheduler started.")
