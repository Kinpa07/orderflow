import pytest

@pytest.fixture(autouse=True)
def clean_db():
    from db.storage import temp_db_tenants, temp_db_orders

    yield 

    # Clear the temporary databases before each test
    temp_db_tenants.clear()
    temp_db_orders.clear()

