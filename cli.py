import json
import os
from datetime import datetime

import httpx
import typer

BASE_URL = os.environ.get("ORDERFLOW_API_URL", "http://localhost:8000")


app = typer.Typer()
tenants_app = typer.Typer()
orders_app = typer.Typer()
app.add_typer(tenants_app, name="tenants")
app.add_typer(orders_app, name="orders")


def _handle_response(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
        raise typer.Exit(code=1)

    typer.echo(response.json())


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
    with httpx.Client() as client:
        try:
            response = client.post(
                f"{BASE_URL}/tenants/",
                json={
                    "company_name": name,
                    "contact_name": contact_name,
                    "email": email,
                    "phone": phone,
                    "config": json.loads(config),
                },
            )
            _handle_response(response)
        except httpx.RequestError as e:
            typer.echo(f"Connection Error: {e}", err=True)
            raise typer.Exit(code=1)


@orders_app.command()
def submit(
    tenant_id: int = typer.Option(
        ...,
        "--tenant",
        help="Tenant ID",
    ),
    data: str = typer.Option(
        ...,
        help=(
            "data for the order, currenlty only price is supported, "
            'format: {"price": 50.0}'
        ),
    ),
    api_key: str = typer.Option(
        ...,
        help="API key",
    ),
) -> None:

    with httpx.Client() as client:
        try:
            response = client.post(
                f"{BASE_URL}/tenants/{tenant_id}/orders/",
                json=json.loads(data),
                headers={"api-key": api_key},
            )
        except httpx.RequestError as e:
            typer.echo(f"Connection Error: {e}", err=True)
            raise typer.Exit(code=1)
        _handle_response(response)


@orders_app.command()
def status(
    tenant_id: int = typer.Option(
        ...,
        "--tenant",
        help="Tenant ID",
    ),
    order_id: int = typer.Option(
        ...,
        "--order",
        help="Order ID",
    ),
    api_key: str = typer.Option(
        ...,
        help="API key",
    ),
) -> None:
    with httpx.Client() as client:
        try:
            response = client.get(
                f"{BASE_URL}/tenants/{tenant_id}/orders/{order_id}",
                headers={"api-key": api_key},
            )
        except httpx.RequestError as e:
            typer.echo(f"Connection Error: {e}", err=True)
            raise typer.Exit(code=1)
        _handle_response(response)


@orders_app.command(name="list")
def list_orders(
    tenant_id: int = typer.Option(
        ...,
        "--tenant",
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
        try:
            response = client.get(
                f"{BASE_URL}/tenants/{tenant_id}/orders/",
                headers={"api-key": api_key},
                params={
                    k: v
                    for k, v in {
                        "page": page,
                        "cursor_created_at": cursor_created_at.isoformat()
                        if cursor_created_at
                        else None,
                        "cursor_id": cursor_id,
                        "status": status,
                        "limit": limit,
                    }.items()
                    if v is not None
                },
            )
        except httpx.RequestError as e:
            typer.echo(f"Connection Error: {e}", err=True)
            raise typer.Exit(code=1)
        _handle_response(response)
