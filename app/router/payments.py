from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Query
from sqlalchemy.orm import Session
import random
from .. database import get_db
from .. import models, schemas
import stripe
from .. config import settings
import logging
import json
from typing import List, Optional
from datetime import datetime, timedelta

from ..logger import logger

# logging.basicConfig(level=logging.DEBUG)

# logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])

def transaction_to_dict(transaction):
    return {
        "id": transaction.id,
        "transaction_id": transaction.transaction_id,
        "payment_method": transaction.payment_method,
        "amount": transaction.payment_link.amount,
        "currency": transaction.payment_link.currency,
        "status": transaction.status,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat()   
    }

@router.get('/transactions', status_code=status.HTTP_200_OK)
def get_transactions(
    db: Session = Depends(get_db), 
    date: Optional[str] = Query(None, description="Filter By Date (YYYY-MM-DD)"),
    currency: Optional[str] = Query(None, description = 'Filter by Currency'),
    transaction_status: Optional[str] = Query(None, description="Filter by transaction status")
):
    # base query
    logger.info("Fetching transactions with filters - Date: %s, Currency: %s, Status: %s", date, currency, transaction_status)
    query = db.query(models.Transaction)
    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            next_day = parsed_date + timedelta(days=1)
            query = query.filter(models.Transaction.created_at >= parsed_date, models.Transaction.created_at < next_day)
        except ValueError:
             logger.error("Invalid date format: %s", date)
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format")
    
    if currency:
        query = query.join(models.Transaction.payment_link).filter(models.PaymentLink.currency == currency)
    
    if transaction_status:
        query = query.filter(models.Transaction.status == transaction_status)
    transactions = query.all()
    logger.info("Retrieved %d transactions", len(transactions))
    return {
        "transactions": [transaction_to_dict(transaction) for transaction in transactions]
    }

@router.post("/create-transaction/{link_id}", status_code=status.HTTP_201_CREATED)
def create_transaction(link_id: int, db: Session = Depends(get_db)):
    payment_link = db.query(models.PaymentLink).filter(models.PaymentLink.id == link_id).first()
    if not payment_link:
        logger.warning("Payment Link ID %d not found", link_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment Link not found")

    # Create a new transaction with status 'pending'
    transaction_id = "txn_" + str(random.randint(100000,9999999))
    new_transaction = models.Transaction(
        payment_link_id=link_id,
        transaction_id=transaction_id,
        status="pending"
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    logger.info("Created new transaction with ID %s", transaction_id)
    # Create a Stripe Checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": payment_link.currency,
                    "product_data": {
                        "name": payment_link.description,
                    },
                    "unit_amount": int(payment_link.amount * 100),
                },
                "quantity": 1,
            },
        ],
        mode="payment",
        success_url=f"{settings.client_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.client_url}/cancel",
        metadata= {
            "transaction_id": transaction_id
        }
    )
    logger.info("Stripe session created for transaction ID %s", transaction_id)
    return {"transaction_id": transaction_id, "url": session.url}

    

@router.post("/{link_id}", status_code=status.HTTP_201_CREATED)
def create_payment_transaction(link_id: int, payment_method: str, db: Session = Depends(get_db)):
    # check that payment link exists
    payment_link = db.query(models.PaymentLink).filter(models.PaymentLink.id == link_id).first()

    if not payment_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment Link not found")
    
    # payment gateway
    transaction_id = "txn_" + str(random.randint(100000,9999999))
    status = "success"

    new_transaction = models.Transaction(payment_link_id=link_id, transaction_id=transaction_id, status=status, payment_method=payment_method)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction

@router.get('/status/{transaction_id}', response_model=schemas.TransactionOut)
def get_transaction_status(transaction_id: str, db: Session = Depends(get_db)):
    """Retrieve the status of a specific transaction"""
    logger.info("Fetching status for transaction ID %s", transaction_id)
    transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()
    if not transaction:
        logger.warning("Transaction ID %s not found", transaction_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction

@router.post("/webhook/")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe webhook endpoint to update transaction status based on Stripe events"""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    # Verify the webhook signature
    try:
        
        event = stripe.Event.construct_from(json.loads(payload), settings.stripe_key)
        
    except ValueError as e:
        # Invalid payload
        logger.error("Invalid payload for Stripe webhook")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error("Invalid signature for Stripe webhook")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    logger.info("Stripe event received: %s", event["type"])
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]  # Contains the checkout session object

        # Retrieve the transaction based on session.id
        transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == session["metadata"]["transaction_id"]).first()
        if transaction:
            transaction.status = "success"
            transaction.payment_method = "credit_card"
            db.commit()
            logger.info("Transaction ID %s marked as success", transaction.transaction_id)
        else:
            # Handle the case where the transaction is not found
            logger.warning("Transaction ID not found for session: %s", session["metadata"]["transaction_id"])
            print("Transaction not found for session:", session["metadata"]["transaction_id"])
    
    elif event["type"] == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        
        # Retrieve the transaction based on session.id
        transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == session["metadata"]["transaction_id"]).first()
        if transaction:
            transaction.status = "failure"  # Update the status to failure
            db.commit()
            logger.info("Transaction ID %s marked as failure", transaction.transaction_id)
        else:
            # Handle the case where the transaction is not found
           logger.warning("Transaction ID not found for session: %s", session["metadata"]["transaction_id"])
    
    # Other event types can be handled here

    return {"status": "success"}
