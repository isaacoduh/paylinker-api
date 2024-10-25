from fastapi import FastAPI, Body, status, HTTPException, Response, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from random import randrange
from . import models
from .database import engine, get_db
from .router import auth, payment_links, payments, dashboard
import os
import stripe
from .config import settings



if settings.env == "production":
    origins = [
        "https://paylinker-web.vercel.app",
        "https://paylinker-web.vercel.app/pay"
    ]
else:
    origins = ["*"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
stripe.api_key = settings.stripe_key
models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(payment_links.router)
app.include_router(payments.router)


@app.get('/')
def root():
    return {"message": "Welcome to Paylinker API"}

