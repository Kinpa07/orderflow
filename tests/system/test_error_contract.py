from collections.abc import Callable

import httpx
from httpx import AsyncClient

from schemas.order import OrderCreate


def assert_error_shape(response: httpx.Response) -> None:
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]


async def test_no_authentication(
    client: AsyncClient, make_order: Callable[..., OrderCreate]
) -> None:
    response = await client.post("/tenants/1/orders/", json=make_order().model_dump())
    assert response.status_code == 401
    assert_error_shape(response)


async def test_tenant_id_missmatch(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> None:
    api_key, _ = tenant_credentials
    response = await client.post(
        "/tenants/15/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
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


async def test_create_tenant_invalid_body_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tenants/", json={"company_name": "Test Company"})
    assert response.status_code == 422
    assert_error_shape(response)
    assert all("loc" in d and "msg" in d for d in response.json()["error"]["details"])

