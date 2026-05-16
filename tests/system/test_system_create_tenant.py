from httpx import AsyncClient

from schemas.tenant import TenantResponse


async def test_create_tenant(
    client: AsyncClient,
) -> None:
    tenant_response = await client.post(
        "/tenants/",
        json={
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "email": "john.doe@testcompany.com",
            "phone": "1234567890",
            "config": {"maximum_price": 100.0},
        },
    )

    assert tenant_response.status_code == 200
    TenantResponse.model_validate(tenant_response.json())
