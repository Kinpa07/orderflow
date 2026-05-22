import os

from redis.asyncio import Redis

from config import REDIS_MAX_CONNECTIONS

REDIS_URL = os.environ.get("REDIS_URL", "")

if not REDIS_URL:
    raise ValueError("REDIS_URL is not set")

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=REDIS_MAX_CONNECTIONS,
)
