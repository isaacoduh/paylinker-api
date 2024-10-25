from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
import random
from .. database import get_db
from .. import models, schemas
import stripe
from .. config import settings
import logging
import json

# logging.basicConfig(level=logging.DEBUG)

# logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("/create-transaction/{link_id}", status_code=status.HTTP_201_CREATED)
def create_transaction(link_id: int, db: Session = Depends(get_db)):
    payment_link = db.query(models.PaymentLink).filter(models.PaymentLink.id == link_id).first()
    if not payment_link:
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
    transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction with transaction ID not found!")
    
    return transaction

@router.post("/webhook/")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    event = None

    # Verify the webhook signature
    try:
        
        event = stripe.Event.construct_from(json.loads(payload), settings.stripe_key)
        
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    # print("event received is", event)
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]  # Contains the checkout session object

        # Retrieve the transaction based on session.id
        transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == session["metadata"]["transaction_id"]).first()
        if transaction:
            transaction.status = "success"
            transaction.payment_method = "credit_card"
            db.commit()
        else:
            # Handle the case where the transaction is not found
            print("Transaction not found for session:", session["metadata"]["transaction_id"])
    
    elif event["type"] == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        
        # Retrieve the transaction based on session.id
        transaction = db.query(models.Transaction).filter(models.Transaction.transaction_id == session["metadata"]["transaction_id"]).first()
        if transaction:
            transaction.status = "failure"  # Update the status to failure
            db.commit()
        else:
            # Handle the case where the transaction is not found
            print("Transaction not found for session:", session["metadata"]["transaction_id"])
    
    # Other event types can be handled here

    return {"status": "success"}
