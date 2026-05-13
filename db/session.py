import os
import time
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from structlog import get_logger

logger = get_logger()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


class TimedAsyncSession(AsyncSession):
    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = await super().execute(statement, *args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        logger.info(
            "SQL Query",
            duration_ms=round(duration, 2),
            statement=str(statement).strip()[:200],
        )
        return result


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=TimedAsyncSession,
    expire_on_commit=False,
)
