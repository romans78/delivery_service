from redis.asyncio import Redis
import os
import logging

redis_client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Creates or returns connection to redis
async def get_redis_client() -> Redis:
    """
        Provides a Redis client instance.

        Creates a new Redis connection on the first call and reuses the same instance
        for any later calls.

        Returns:
            Redis: Async Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
    return redis_client
