from conftest import make_tenant
from httpx import AsyncClient

from schemas.tenant import TenantResponse


async def test_create_tenant(
    client: AsyncClient,
) -> None:
    tenant_response = await client.post(
        "/tenants/",
        json=make_tenant().model_dump(),
    )

    assert tenant_response.status_code == 200
    TenantResponse.model_validate(tenant_response.json())
