import httpx
from httpx import AsyncClient


def assert_error_shape(response: httpx.Response) -> None:
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]


async def test_no_authentication(client: AsyncClient) -> None:
    response = await client.post("/tenants/1/orders/", json={"price": 50.0})
    assert response.status_code == 401
    assert_error_shape(response)


async def test_tenant_id_missmatch(
    client: AsyncClient, tenant_credentials: tuple[str, int]
) -> None:
    api_key, tenant_id = tenant_credentials
    response = await client.post(
        "/tenants/15/orders/", json={"price": 50.0}, headers={"api-key": api_key}
    )
    assert response.status_code == 403
    assert_error_shape(response)


async def test_price_exceeds_maximum(
    client: AsyncClient, tenant_credentials: tuple[str, int]
) -> None:
    api_key, tenant_id = tenant_credentials
    response = await client.post(
        f"/tenants/{tenant_id}/orders/",
        json={"price": 150.0},
        headers={"api-key": api_key},
    )
    assert response.status_code == 400
    assert_error_shape(response)
