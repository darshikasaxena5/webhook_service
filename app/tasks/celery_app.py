import os
from celery import Celery
from celery.schedules import crontab # Import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

redis_url_full = os.environ.get("REDIS_URL", "redis://redis:6379/0")
print(f"[celery_app.py] Raw REDIS_URL from env: {redis_url_full}")

# Attempt to remove the default username if present for Celery compatibility
redis_url_celery = redis_url_full
if redis_url_full.startswith("redis://default:"): 
    redis_url_celery = redis_url_full.replace("redis://default:", "redis://:", 1)
    print(f"[celery_app.py] Modified URL for Celery: {redis_url_celery}")

# Define Celery app
# The first argument is the name of the current module, helpful for auto-discovery
# The broker is where Celery sends messages, backend is where results are stored
celery_app = Celery(
    "worker",
    include=[
        "app.tasks.delivery", 
        "app.tasks.cleanup" # Add cleanup tasks module
    ]
)
celery_app.conf.broker_url = redis_url_celery 
celery_app.conf.result_backend = redis_url_celery
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
