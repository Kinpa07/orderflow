from pydantic import ValidationError
from schemas.tenant import TenantConfig
import pytest


def test_valid_config() -> None:
    config = TenantConfig(maximum_price=150.0)
    assert config.maximum_price == 150.0


def test_invalid_config() -> None:
    with pytest.raises(ValidationError) as _:
        TenantConfig(maximum_price="not_a_float")  # type: ignore[arg-type]
