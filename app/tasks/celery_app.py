import os
from celery import Celery
from celery.schedules import crontab # Import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

# Define Celery app
# The first argument is the name of the current module, helpful for auto-discovery
# The broker is where Celery sends messages, backend is where results are stored
celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.delivery", 
        "app.tasks.cleanup" # Add cleanup tasks module
    ]
)

# Optional Celery configuration settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Add other configurations like task queues if needed later
)

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'cleanup-old-logs-daily': {
        'task': 'app.tasks.cleanup.cleanup_old_logs', # Task path
        'schedule': crontab(hour=1, minute=30),  # Run daily at 1:30 AM UTC (adjust as needed)
        # Alternatively, use timedelta: 'schedule': timedelta(hours=24),
    },
}

if __name__ == '__main__':
    celery_app.start() 