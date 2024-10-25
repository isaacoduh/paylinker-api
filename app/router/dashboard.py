from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
from ..database import get_db
from .. import models, schemas
from .oauth2 import get_current_user
import asyncio
import json

router = APIRouter(prefix='/api/dashboard', tags=["Dashboard"])

@router.get("/")
def get_dashboard_data(db:Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    total_earnings = calculate_total_earnings(db, current_user.id)
    transactions = get_transactions(db, current_user.id)
    performance = get_link_performance(db, current_user.id)

    return {
        "total_earnings": total_earnings,
        "transactions": transactions,
        "performance": performance    
    }


def calculate_total_earnings(db: Session, user_id: int):
    earnings = defaultdict(float)

    transactions = db.query(models.Transaction).join(models.PaymentLink).filter(models.PaymentLink.user_id == user_id).all()
    for transaction in transactions:
        if transaction.status == "success":
            payment_link = db.query(models.PaymentLink).filter(models.PaymentLink.id == transaction.payment_link_id).first()
            earnings[payment_link.currency] += payment_link.amount
    return earnings

def get_transactions(db: Session, user_id: int, period: str = "last_week"):
    # Define a mapping of periods to their respective timedelta
    period_mapping = {
        "last_day": timedelta(days=1),
        "last_week": timedelta(weeks=1),
        "last_year": timedelta(days=365),
    }

    # Calculate the start date based on the provided period or default to last 30 days
    start_date = datetime.utcnow() - period_mapping.get(period, timedelta(days=30))

    # Query transactions
    transactions = (
        db.query(models.Transaction)
        .join(models.PaymentLink)
        .filter(models.PaymentLink.user_id == user_id)
        .filter(models.Transaction.created_at >= start_date)
        .all()
    )
    
    return transform_transactions(transactions)
    
    # transactions = (db.query(models.Transaction).join(models.PaymentLink).filter(models.PaymentLink.user_id == user_id).filter(models.Transaction.created_at >= start_date).all())
    # return [transaction_to_dict(transaction) for transaction in transactions]

def transform_transactions(transactions):
    # Transform the list of transaction objects into the desired format
    earnings = {}
    
    for transaction in transactions:
        date_str = transaction.created_at.date().isoformat()  # Get the date as a string
        currency = transaction.payment_link.currency
        amount = transaction.payment_link.amount
        
        if date_str not in earnings:
            earnings[date_str] = {"date": date_str}
        
        earnings[date_str][currency] = amount

    # Convert the earnings dictionary to a list
    return list(earnings.values())

def transaction_to_dict(transaction):
    return {
        "id": transaction.id,
        "amount": transaction.payment_link.amount,
        "currency": transaction.payment_link.currency,
        "status": transaction.status,
        "created_at": transaction.created_at.isoformat()    
    }

def get_link_performance(db: Session, user_id: int):
    link_performance = db.query(models.PaymentLink).filter(models.PaymentLink.user_id == user_id).all()
    performance_data = []
    for link in link_performance:
        performance_data.append({
            "link_id": link.id, 
            "description": link.description,
            "total_transactions": db.query(models.Transaction).filter(models.Transaction.payment_link_id == link.id).count(),
            "successful_transactions": db.query(models.Transaction).filter(models.Transaction.payment_link_id == link.id, models.Transaction.status == "success").count(),
            "total_amount": sum(t.payment_link.amount for t in link.transactions if t.status == "success")
        })
    return performance_data

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            # fetch the latest earnings data
            total_earnings = calculate_total_earnings(db, user_id)
            # send updated earnings data to the client
            await websocket.send_text(json.dumps({
                "total_earnings": total_earnings,
                "timestamp": datetime.utcnow().isoformat()
                }))
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected")