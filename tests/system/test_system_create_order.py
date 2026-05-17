from collections.abc import Callable

import pytest
from httpx import AsyncClient

from schemas.order import OrderCreate, OrderResponse


async def test_create_order(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )
    assert order_response.status_code == 200
    OrderResponse.model_validate(order_response.json())


@pytest.mark.parametrize(
    "price,expected_status",
    [
        (50.0, 200),
        (150.0, 400),
        (100.0, 200),
        (
            0.0,
            200,
        ),
        (
            None,
            422,
        ),
    ],
)
async def test_price_expected_status(
    client: AsyncClient,
    tenant_credentials: tuple[str, int],
    price: float | None,
    expected_status: int,
) -> None:

    body = {} if price is None else {"price": price}
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json=body,
        headers={"api-key": api_key},
    )
    assert order_response.status_code == expected_status
