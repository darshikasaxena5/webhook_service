import os
import redis
import json
import uuid
from typing import Optional
from dotenv import load_dotenv
from app.models.subscription import Subscription # Import the model to be cached

load_dotenv()

redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL_SECONDS = 60 * 5 # Cache subscriptions for 5 minutes

# Initialize Redis client connection
# decode_responses=True helps avoid manual decoding later
try:
    redis_cache = redis.from_url(redis_url, decode_responses=True)
    redis_cache.ping() # Verify connection
    print("Redis cache connection successful.")
except redis.exceptions.ConnectionError as e:
    print(f"Redis cache connection failed: {e}")
    redis_cache = None # Set to None if connection fails

def get_cache() -> Optional[redis.Redis]:
    """Dependency function to get the Redis cache client."""
    # In a real app, you might want more robust connection handling/pooling
    if redis_cache and redis_cache.ping(): # Check connection is still alive
         return redis_cache
    else:
         print("Attempting to reconnect to Redis cache...")
         try:
             new_cache = redis.from_url(redis_url, decode_responses=True)
             new_cache.ping()
             print("Redis cache reconnected.")
             return new_cache
         except redis.exceptions.ConnectionError:
             print("Redis cache reconnection failed.")
             return None # Return None if connection cannot be established

# --- Cache Helper Functions --- 

def _get_subscription_cache_key(subscription_id: uuid.UUID) -> str:
    return f"subscription:{subscription_id}"

def get_subscription_from_cache(cache: redis.Redis, subscription_id: uuid.UUID) -> Optional[Subscription]:
    """Tries to retrieve a subscription from the cache."""
    if not cache:
        return None
    key = _get_subscription_cache_key(subscription_id)
    try:
        cached_data = cache.get(key)
        if cached_data:
            print(f"[Cache HIT] Found subscription {subscription_id} in cache.")
            # Deserialize JSON string back to Pydantic model
            return Subscription(**json.loads(cached_data))
        else:
            print(f"[Cache MISS] Subscription {subscription_id} not in cache.")
    except redis.exceptions.RedisError as e:
        print(f"Redis error getting cache for {key}: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error for cached subscription {subscription_id}: {e}")
        # Consider deleting the invalid cache entry
        try:
            cache.delete(key)
        except redis.exceptions.RedisError:
            pass # Ignore delete error
    return None

def set_subscription_in_cache(cache: redis.Redis, subscription: Subscription):
    """Stores a subscription in the cache with a TTL."""
    if not cache:
        return
    key = _get_subscription_cache_key(subscription.id)
    try:
        # Serialize Pydantic model to JSON string
        # Use .model_dump_json() for Pydantic v2
        cache.set(key, subscription.model_dump_json(), ex=CACHE_TTL_SECONDS)
        print(f"[Cache SET] Stored subscription {subscription.id} in cache (TTL: {CACHE_TTL_SECONDS}s).")
    except redis.exceptions.RedisError as e:
        print(f"Redis error setting cache for {key}: {e}")

def delete_subscription_from_cache(cache: redis.Redis, subscription_id: uuid.UUID):
    """Removes a subscription from the cache."""
    if not cache:
        return
    key = _get_subscription_cache_key(subscription_id)
    try:
        deleted_count = cache.delete(key)
        if deleted_count > 0:
            print(f"[Cache DEL] Deleted subscription {subscription_id} from cache.")
    except redis.exceptions.RedisError as e:
        print(f"Redis error deleting cache for {key}: {e}") 