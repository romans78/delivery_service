from redis.asyncio import Redis
import os
import logging

redis_client = None



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# создает или возвращает подключение к Redis
async def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
    return redis_client

