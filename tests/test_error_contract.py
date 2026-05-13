import httpx
from httpx import AsyncClient


def assert_error_shape(response: httpx.Response) -> None:
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]


async def create_tenant_and_test_order_creation(client: AsyncClient) -> tuple[str, int]:
    # Create a tenant with a valid API key
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
    api_key = tenant_response.json()["api_key"]
    id = tenant_response.json()["id"]
    return api_key, id


async def test_no_authentication(client: AsyncClient) -> None:
    response = await client.post("/tenants/1/orders/", json={"price": 50.0})
    assert response.status_code == 401
    assert_error_shape(response)


async def test_tenant_id_missmatch(client: AsyncClient) -> None:
    api_key, tenant_id = await create_tenant_and_test_order_creation(client)
    response = await client.post(
        "/tenants/15/orders/", json={"price": 50.0}, headers={"api-key": api_key}
    )
    assert response.status_code == 403
    assert_error_shape(response)


async def test_price_exceeds_maximum(client: AsyncClient) -> None:
    api_key, tenant_id = await create_tenant_and_test_order_creation(client)
    response = await client.post(
        f"/tenants/{tenant_id}/orders/",
        json={"price": 150.0},
        headers={"api-key": api_key},
    )
    assert response.status_code == 400
    assert_error_shape(response)
