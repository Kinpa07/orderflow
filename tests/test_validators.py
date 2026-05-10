from pydantic import ValidationError
from schemas.tenant import TenantCreate, TenantConfig
import pytest


def test_tenant_create_email_validation_without_at_symbol() -> None:
    with pytest.raises(ValidationError) as _:
        TenantCreate(
            company_name="Test Company",
            contact_name="John Doe",
            email="invalidemail.com",
            phone="1234567890",
            config=TenantConfig(maximum_price=100.0),
        )


def test_tenant_create_email_validation_without_company_name() -> None:
    with pytest.raises(ValidationError) as _:
        TenantCreate(
            company_name="Test Company",
            contact_name="John Doe",
            email="john.c.calhoun@examplepetstore.com",
            phone="1234567890",
            config=TenantConfig(maximum_price=100.0),
        )


def test_tenant_create_valid_email() -> None:
    tenant = TenantCreate(
        company_name="Test Company",
        contact_name="John Doe",
        email="john.c.calhoun@testcompany.com",
        phone="1234567890",
        config=TenantConfig(maximum_price=100.0),
    )
    assert tenant.email == "john.c.calhoun@testcompany.com"
    assert tenant.company_name == "Test Company"
    assert tenant.contact_name == "John Doe"
    assert tenant.phone == "1234567890"
    assert tenant.config.maximum_price == 100.0


def test_valid_config() -> None:
    config = TenantConfig(maximum_price=150.0)
    assert config.maximum_price == 150.0


def test_invalid_config() -> None:
    with pytest.raises(ValidationError) as _:
        TenantConfig(maximum_price="not_a_float")  # type: ignore[arg-type]
