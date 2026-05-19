import os

WEBHOOK_RETRY_COUNT = int(os.environ.get("WEBHOOK_RETRY_COUNT", "3"))
WEBHOOK_TIMEOUT = int(os.environ.get("WEBHOOK_TIMEOUT", "5"))
TENANT_CACHE_TTL = int(os.environ.get("TENANT_CACHE_TTL", "60"))
