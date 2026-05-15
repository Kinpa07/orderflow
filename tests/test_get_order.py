from httpx import AsyncClient


async def test_get_order(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    order_id: int,
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.get(
        f"/tenants/{tena_id}/orders/{order_id}",
        headers={"api-key": api_key},
    )
    assert order_response.status_code == 200
    assert order_id == order_response.json()["id"]


async def test_get_order_not_found(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.get(
        f"/tenants/{tena_id}/orders/2912880",
        headers={"api-key": api_key},
    )
    assert order_response.status_code == 404
    assert "error" in order_response.json()
    assert order_response.json()["error"]["message"] == "Order not found"


async def test_two_tenants_same_order(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    order_id: int,
) -> None:
    api_key, tena_id = tenant_credentials

    second_tenant_response = await client.post(
        "/tenants/",
        json={
            "company_name": "Vesko Corp",
            "contact_name": "Veselin Iliev",
            "email": "veneli93@abv.bg",
            "phone": "1234567890",
            "config": {"maximum_price": 200.0},
        },
    )
    second_tenant_api_key = second_tenant_response.json()["api_key"]

    order_response = await client.get(
        f"/tenants/{tena_id}/orders/{order_id}",
        headers={"api-key": second_tenant_api_key},
    )

    assert order_response.status_code == 403
    assert order_response.json()["error"]["message"] == "Forbidden: Tenant ID mismatch"
