from fastapi import FastAPI, Body, status, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from random import randrange
from . import models
from .database import engine, get_db
from .router import auth, payment_links


models.Base.metadata.create_all(bind=engine)
origins = ["*"]


app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(payment_links.router)



my_links = [
    {
        "id": 1,
        "amount": 50.0,
        "currency": "USD",
        "description": "Payment for subscription",
        "expiration_date": "2024-10-30"
    },
    {
        "id": 2,
        "amount": 150.75,
        "currency": "EUR",
        "description": "Consultation fee",
        "expiration_date": "2024-11-06"
    },
    {
        "id": 3,
        "amount": 500.0,
        "currency": "GBP",
        "description": "Payment for software license",
        "expiration_date": "2024-12-06"
    },
    {
        "id": 4,
        "amount": 20.99,
        "currency": "USD",
        "description": "E-book purchase",
        "expiration_date": None
    }
]


class PaymentLink(BaseModel):
    amount: float
    currency: str
    description: str
    expiration_date: Optional[str] = None


def generate_expiration(days_from_now: int):
    return (datetime.now() + timedelta(days=days_from_now)).strftime('%Y-%m-%d')


def find_link(id: int):
    for link in my_links:
        if link["id"] == id:
            return link
    return None


def find_index_link(id: int):
    for index, link in enumerate(my_links):
        if link["id"] == id:
            return index


@app.get('/')
def root():
    return {"message": "Welcome to Paylinker API"}


@app.get("/links")
def get_payment_links():
    return {"data": my_links}


@app.get('/links/{id}')
def get_link(id: str, response: Response):
    id = int(id)
    link = find_link(id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link with ID {id} not found!")
    return {"data": link}


@app.post('/create-link', status_code=status.HTTP_201_CREATED)
def create_payment_link(payment_link: PaymentLink):
    payment_link_dict = payment_link.dict()
    payment_link_dict["id"] = randrange(0, 100000)
    my_links.append(payment_link_dict)
    return {"data": payment_link_dict}


@app.delete('/links/{id}')
def delete_link(id: int):
    index = find_index_link(id)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link with ID {id} not found!")
    my_links.pop(index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put('/links/{id}')
def update_link(id: int, link: PaymentLink):
    index = find_index_link(id)
    if index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link with ID {id} not found!")
    payment_link_dict = link.dict()
    payment_link_dict["id"] = id
    my_links[index] = payment_link_dict
    return {"data": payment_link_dict}