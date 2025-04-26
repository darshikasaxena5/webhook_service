import os
from datetime import datetime, timedelta, timezone
from app.tasks.celery_app import celery_app
from app.db.client import get_db
from app.db import attempts as db_attempts
from dotenv import load_dotenv

load_dotenv()

# Get retention period from environment variable (default to 72 hours)
LOG_RETENTION_HOURS = int(os.environ.get("LOG_RETENTION_HOURS", 72))

@celery_app.task
def cleanup_old_logs():
    """Periodic task to delete delivery attempt logs older than the retention period."""
    print(f"[Periodic Task] Running cleanup_old_logs (retention: {LOG_RETENTION_HOURS} hours)")
    db = get_db()
    if LOG_RETENTION_HOURS <= 0:
        print("Log retention is disabled (LOG_RETENTION_HOURS <= 0).")
        return
        
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=LOG_RETENTION_HOURS)
        deleted_count = db_attempts.delete_attempts_older_than(db, cutoff_time)
        print(f"[Periodic Task] Log cleanup finished. Deleted {deleted_count} records.")
    except Exception as e:
        print(f"[Periodic Task Error] Failed during log cleanup: {e}")
        # Depending on severity, might want to raise to trigger alerts 