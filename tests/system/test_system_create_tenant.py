from collections.abc import Callable

from httpx import AsyncClient

from schemas.tenant import TenantCreate, TenantResponse


async def test_create_tenant(
    client: AsyncClient,
    make_tenant: Callable[..., TenantCreate],
) -> None:
    tenant_response = await client.post(
        "/tenants/",
        json=make_tenant().model_dump(),
    )

    assert tenant_response.status_code == 200
    TenantResponse.model_validate(tenant_response.json())
