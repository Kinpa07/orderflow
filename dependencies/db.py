from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()   # commit if everything went well
        except Exception:
            await session.rollback() # rollback on any error
            raise                    # re-raise so FastAPI handles it