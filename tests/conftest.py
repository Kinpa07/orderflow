from collections.abc import Generator

import pytest

@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    from db.storage import temp_db_tenants, temp_db_orders

    yield 

    # Clear the temporary databases after each test to ensure test isolation
    temp_db_tenants.clear()
    temp_db_orders.clear()

