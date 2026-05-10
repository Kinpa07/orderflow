import pytest
from fastapi import testclient
from main import app

client = testclient.TestClient(app)

def assert_error_shape(response):
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]

def create_tenant_and_test_order_creation() :
    # Create a tenant with a valid API key
    tenant_response = client.post("/tenants/", json={"company_name": "Test Company",
                                                      "contact_name": "John Doe", "email": "john.doe@testcompany.com", 
                                                      "phone": "1234567890", "config": {"maximum_price": 100.0}})
    api_key = tenant_response.json()["api_key"]
    id = tenant_response.json()["id"]
    return api_key, id


def test_no_authentication():
        response = client.post("/tenants/1/orders/", json={"price": 50.0})
        assert response.status_code == 401
        assert_error_shape(response)

def test_valid_authentication_not_existing_tenant():
    api_key, tenant_id = create_tenant_and_test_order_creation()
    response = client.post("/tenants/15/orders/", json={"price": 50.0}, headers={"api-key": api_key})
    assert response.status_code == 404
    assert_error_shape(response)

def test_price_exceeds_maximum():
    api_key, tenant_id = create_tenant_and_test_order_creation()
    response = client.post(f"/tenants/{tenant_id}/orders/", json={"price": 150.0}, headers={"api-key": api_key})
    assert response.status_code == 400
    assert_error_shape(response)