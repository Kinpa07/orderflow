from httpx import AsyncClient

from schemas.order import OrderResponse


async def test_create_order(
    client: AsyncClient, tenant_credentials: tuple[str, int]
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json={"price": 50.0},
        headers={"api-key": api_key},
    )
    assert order_response.status_code == 200
    OrderResponse.model_validate(order_response.json())
