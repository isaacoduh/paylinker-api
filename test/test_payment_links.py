import pytest
from app import schemas
from sqlalchemy.orm import Session
from jose import jwt
from app.config import settings

def test_create_payment_link(authorized_client):
    response = authorized_client.post("/api/payment-links/", json={
        "amount": 50.0,
        "currency": "USD",
        "description": "Test Link",
        "expiration_date": "2024-12-31T23:59:59"
    })
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["amount"] == 50.0
    assert response_data["currency"] == "USD"
    assert response_data["description"] == "Test Link"

def test_get_payment_link_by_code(authorized_client, create_payment_link):
    create_response = create_payment_link()
    created_link = create_response.json()
    
    response = authorized_client.get(f"/api/payment-links/{created_link['link_code']}")
    assert response.status_code == 200
    fetched_link = response.json()
    assert fetched_link["link_code"] == created_link["link_code"]

def test_get_payment_link_by_id(authorized_client, create_payment_link):
    create_response = create_payment_link()
    created_link = create_response.json()
    response = authorized_client.get(f"/api/payment-links/get-by-id/{created_link['id']}")
    assert response.status_code == 200
    fetched_link = response.json()
    assert fetched_link["id"] == created_link["id"]

def test_update_payment_link(authorized_client, create_payment_link):
    create_response = create_payment_link()
    created_link = create_response.json()
    update_data = {"amount": 75.0, "currency": "GBP", "description": "Euro Link",
        "expiration_date": "2024-12-31T23:59:59"}
    response = authorized_client.put(f"/api/payment-links/{created_link['id']}", json=update_data)
    assert response.status_code == 200
    updated_link = response.json()
    assert updated_link["amount"] == 75.0
    assert updated_link["description"] == "Euro Link"

def test_delete_payment_link(authorized_client, create_payment_link):
    create_response = create_payment_link()
    created_link = create_response.json()
    response = authorized_client.delete(f"/api/payment-links/{created_link['id']}")
    assert response.status_code == 204
    # Verify deletion by attempting to fetch again
    response = authorized_client.get(f"/api/payment-links/{created_link['id']}")
    assert response.status_code == 404

def test_filter_payment_links_by_currency(authorized_client, create_payment_link):
    # Create a few payment links with different currencies
    create_payment_link()
    authorized_client.post("/api/payment-links/", json={
        "amount": 200.0,
        "currency": "EUR",
        "description": "Euro Link",
        "expiration_date": "2024-12-31T23:59:59"
    })
    
    # Test filtering by USD currency
    response = authorized_client.get("/api/payment-links/?currency=USD")
    assert response.status_code == 200
    usd_links = response.json()
    for link in usd_links:
        assert link["currency"] == "USD"

