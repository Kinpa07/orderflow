import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from dependencies.db import get_db
from dependencies.redis import get_redis
from main import app
from models.base import Base
from schemas.order import OrderCreate
from schemas.tenant import TenantConfig, TenantCreate

REDIS_URL = os.environ["REDIS_URL"]

DATABASE_URL = os.environ["DATABASE_URL"]

test_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture()
def make_tenant() -> Callable[..., TenantCreate]:
    def _make(**overrides: Any) -> TenantCreate:
        defaults: dict[str, Any] = {
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "email": "john.doe@testcompany.com",
            "phone": "1234567890",
            "config": TenantConfig(maximum_price=100.0),
        }
        defaults.update(overrides)
        return TenantCreate(**defaults)

    return _make


@pytest.fixture()
def make_order() -> Callable[..., OrderCreate]:
    def _make(**overrides: Any) -> OrderCreate:
        defaults = {
            "price": 50.0,
        }
        defaults.update(overrides)
        return OrderCreate(**defaults)

    return _make


@pytest_asyncio.fixture()
async def make_orders(
    client: AsyncClient, tenant_credentials: tuple[str, int]
) -> Callable[[int], Awaitable[None]]:
    async def _make(count: int = 21) -> None:
        for i in range(count):
            await client.post(
                f"/tenants/{tenant_credentials[1]}/orders/",
                json=OrderCreate(price=50.0 + i).model_dump(),
                headers={"api-key": tenant_credentials[0]},
            )

    return _make


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_tables() -> AsyncGenerator[None, None]:
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def tenant_credentials(
    client: AsyncClient, make_tenant: Callable[..., TenantCreate]
) -> tuple[str, int]:
    response = await client.post(
        "/tenants/",
        json=make_tenant().model_dump(),
    )
    return response.json()["api_key"], response.json()["id"]


@pytest_asyncio.fixture
async def order_id(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> int:
    api_key, tenant_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tenant_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )
    return int(order_response.json()["id"])


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Redis, None]:
    client = Redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture
async def client(redis_client: Redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_get_redis() -> Redis:
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
