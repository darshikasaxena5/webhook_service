from supabase import Client
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def get_system_stats(db: Client) -> dict:
    """Retrieves various system statistics for the dashboard."""
    try:
        # 1. Get total subscription count
        # Assuming 'subscriptions' is the table name
        count_res = db.table('subscriptions').select('id', count='exact').execute()
        total_subscriptions = count_res.count

        # 2. Get recent delivery counts (e.g., last 24 hours)
        # Assuming 'webhook_deliveries' is the table name and has 'status' and 'created_at'
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        
        # Count recent successes
        success_res = db.table('webhook_deliveries') \
            .select('id', count='exact') \
            .eq('status', 'success') \
            .gte('created_at', time_threshold.isoformat()) \
            .execute()
        recent_success_count = success_res.count

        # Count recent permanent failures 
        # Assuming 'failed' is the status for permanent failures
        failed_res = db.table('webhook_deliveries') \
            .select('id', count='exact') \
            .eq('status', 'failed') \
            .gte('created_at', time_threshold.isoformat()) \
            .execute()
        recent_failed_count = failed_res.count

        return {
            "total_subscriptions": total_subscriptions,
            "recent_success_count": recent_success_count,
            "recent_failed_count": recent_failed_count,
        }

    except Exception as e:
        logger.error(f"Error fetching system stats: {e}", exc_info=True)
        # Don't crash the endpoint, maybe return zeros or raise specific error
        # For simplicity, re-raising, but consider returning default values
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics from database."
        ) 