from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant


async def test_create_tenant(client: AsyncClient, db_session: AsyncSession) -> None:

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


    record = await db_session.get(Tenant, tenant_response.json()["id"])
    assert record is not None
    assert record.company_name == "Test Company"
    assert record.contact_name == "John Doe"
    assert record.email == "john.doe@testcompany.com"
    assert record.phone == "1234567890"
    assert record.config["maximum_price"] == 100.0
    assert record.api_key == tenant_response.json()["api_key"]
