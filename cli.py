from datetime import datetime

import typer
import httpx
import json


app = typer.Typer()
tenants_app = typer.Typer()
orders_app = typer.Typer()
app.add_typer(tenants_app, name="tenants")
app.add_typer(orders_app, name="orders")


@tenants_app.command()
def create(
    contact_name: str = typer.Option(default="John Doe", help="Contact name"),
    name: str = typer.Option(
        ...,
        help="Tenant name",
    ),
    email: str = typer.Option(
        default="john.doe@testcompany.com",
        help="Tenant email",
    ),
    phone: str = typer.Option(
        default="1234567890",
        help="Tenant phone",
    ),
    config: str = typer.Option(
        default='{"maximum_price": 100.0}',
        help="Tenant config",
    ),
) -> None:
    """Create a new tenant."""
    with httpx.Client() as client:
        response = client.post(
            "http://localhost:8000/tenants/",
            json={
                "company_name": name,
                "contact_name": contact_name,
                "email": email,
                "phone": phone,
                "config": json.loads(config),
            },
        )
        print(response.json())


@orders_app.command()
def submit(
    tenant_id: int = typer.Option(
        ...,
        help="Tenant ID",
    ),
    price: float = typer.Option(
        ...,
        help="Order price",
    ),
    api_key: str = typer.Option(
        ...,
        help="API key",
    ),
) -> None:

    with httpx.Client() as client:
        response = client.post(
            f"http://localhost:8000/tenants/{tenant_id}/orders/",
            json={"price": price},
            headers={"api-key": api_key},
        )
        print(response.json())


@orders_app.command()
def status(
    tenant_id: int = typer.Option(
        ...,
        help="Tenant ID",
    ),
    order_id: int = typer.Option(
        ...,
        help="Order ID",
    ),
    api_key: str = typer.Option(
        ...,
        help="API key",
    ),
) -> None:
    with httpx.Client() as client:
        response = client.get(
            f"http://localhost:8000/tenants/{tenant_id}/orders/{order_id}",
            headers={"api-key": api_key},
        )
        print(response.json())


@orders_app.command()
def list_orders(
    tenant_id: int = typer.Option(
        ...,
        help="Tenant ID",
    ),
    page: int = typer.Option(
        1,
        help="Page number",
    ),
    cursor_created_at: datetime | None = typer.Option(
        None,
        help="Cursor created_at",
    ),
    cursor_id: int | None = typer.Option(
        None,
        help="Cursor id",
    ),
    status: str | None = typer.Option(
        None,
        help="Order status",
    ),
    limit: int = typer.Option(
        20,
        help="Limit",
    ),
    api_key: str = typer.Option(
        ...,
        help="API key",
    ),
) -> None:
    with httpx.Client() as client:
        response = client.get(
            f"http://localhost:8000/tenants/{tenant_id}/orders/",
            headers={"api-key": api_key},
            params={
                k: v
                for k, v in {
                    "page": page,
                    "cursor_created_at": (cursor_created_at),
                    "cursor_id": cursor_id,
                    "status": status,
                    "limit": limit,
                }.items()
                if v is not None
            },
        )

        print(response.json())
