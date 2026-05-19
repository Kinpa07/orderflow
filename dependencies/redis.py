from redis.asyncio import Redis

from db.redis import redis_client


async def get_redis() -> Redis:
    return redis_client
