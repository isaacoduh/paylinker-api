from certifi import contents
from pydantic import BaseModel, EmailStr, conint, ConfigDict, Field
from pydantic.types import conint
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    email: EmailStr
    id: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PaymentLinkCreate(BaseModel):
    amount: float
    currency: str
    description: Optional[str] = Field(None, description="Description for the purpose of the payment link")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date for the payment link")

class PaymentLinkUpdate(BaseModel):
    amount: Optional[float]
    currency: Optional[str]
    description: Optional[str]
    expiration_date: Optional[datetime]

class PaymentLinkOut(BaseModel):
    id: int
    user_id: int
    amount: float
    currency: str
    link_code: str
    description: Optional[str]
    expiration_date: Optional[datetime]
    link_url: Optional[str]

    class Config:
        orm_mode = True

class TransactionOut(BaseModel):
    id: int
    payment_link_id: int
    transaction_id: str
    status: str
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None