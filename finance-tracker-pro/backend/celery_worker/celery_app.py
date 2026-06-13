from celery import Celery
from datetime import datetime, timedelta

# Create Celery app
celery_app = Celery(
    'finance_tracker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['celery_worker.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

# Celery Beat schedule for recurring payments
celery_app.conf.beat_schedule = {
    'process-recurring-payments-every-hour': {
        'task': 'celery_worker.tasks.process_recurring_payments',
        'schedule': 3600.0,  # Run every hour
    },
}
