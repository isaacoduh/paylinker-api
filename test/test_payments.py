import pytest
from app import schemas
from sqlalchemy.orm import Session
from jose import jwt
from app.config import settings


def test_create_transaction(authorized_client, create_payment_link, create_transaction):
    link_response = create_payment_link()
    payment_link = link_response.json()

    # Create a transaction using the mocked function
    transaction = create_transaction(payment_link["id"], status="success")

    # Assertions to verify the transaction details
    assert transaction["payment_link_id"] == payment_link["id"]
    assert transaction["status"] == "success"
    assert transaction["amount"] == 100.0  # Adjust as needed
    assert transaction["id"]  # Ensure transaction ID is generated


def test_filter_transactions_by_status(authorized_client, create_payment_link, create_transaction):
    # Arrange: Create two transactions with different statuses
    link_response = create_payment_link()
    payment_link = link_response.json()
    create_transaction(payment_link["id"], status="success")
    create_transaction(payment_link["id"], status="pending")

    # Act: Fetch transactions filtered by "success" status
    response = authorized_client.get("/api/payments/transactions?transaction_status=success")
    assert response.status_code == 200
    
    # Debug: Print the response to understand its structure
    transactions = response.json()
    
    for transaction in transactions["transactions"]:
        assert transaction["status"] == "success"
