from supabase import Client
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def get_recent_activity(db: Client, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches a combined list of recent activities (subscriptions, attempts)."""
    
    combined_activity = []
    
    try:
        # 1. Fetch recent subscriptions
        # Assuming table 'subscriptions', relevant columns 'id', 'created_at', 'target_url'
        sub_res = db.table('subscriptions') \
            .select('id', 'created_at', 'target_url') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
            
        for sub in sub_res.data:
            combined_activity.append({
                "type": "subscription_created",
                "id": str(sub['id']), # Ensure ID is string
                "timestamp": datetime.fromisoformat(sub['created_at'].replace('Z', '+00:00')), # Parse timestamp
                "details": f"Subscribed: {sub['target_url'][:50]}..." # Example detail string
            })

        # 2. Fetch recent delivery attempts
        # Assuming table 'delivery_attempts', relevant columns 'id', 'timestamp', 'outcome', 'attempt_number', 'delivery_id'
        attempt_res = db.table('delivery_attempts') \
            .select('id', 'timestamp', 'outcome', 'attempt_number', 'delivery_id') \
            .order('timestamp', desc=True) \
            .limit(limit) \
            .execute()
            
        for att in attempt_res.data:
            combined_activity.append({
                "type": "delivery_attempt",
                "id": str(att['id']), # Attempt ID
                "timestamp": datetime.fromisoformat(att['timestamp'].replace('Z', '+00:00')), # Parse timestamp
                "details": f"Delivery {str(att['delivery_id'])[:8]}... Attempt #{att['attempt_number']} - {att['outcome']}" # Example detail
            })

        # 3. Sort combined list by timestamp (descending)
        combined_activity.sort(key=lambda x: x['timestamp'], reverse=True)

        # 4. Return the top N items overall
        return combined_activity[:limit]

    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}", exc_info=True)
        # Return empty list on error for this non-critical endpoint
        return []