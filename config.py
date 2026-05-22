import os

WEBHOOK_RETRY_COUNT = int(os.environ.get("WEBHOOK_RETRY_COUNT", "3"))
WEBHOOK_TIMEOUT = int(os.environ.get("WEBHOOK_TIMEOUT", "5"))
TENANT_CACHE_TTL = int(os.environ.get("TENANT_CACHE_TTL", "60"))

# Postgres connection pool
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "1800"))

# Redis connection pool
REDIS_MAX_CONNECTIONS = int(os.environ.get("REDIS_MAX_CONNECTIONS", "20"))
