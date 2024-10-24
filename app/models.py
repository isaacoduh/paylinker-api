from .database import Base
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, column, ForeignKey, DateTime
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True, server_default=text('now()'))


class PaymentLink(Base):
    __tablename__ = "payment_links"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(Text, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    link_code = Column(String, nullable=False)
    link_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)

    transactions = relationship('Transaction', back_populates="payment_link")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    payment_link_id = Column(Integer, ForeignKey("payment_links.id"))
    transaction_id = Column(String, unique=True, index=True)
    status = Column(String) # e.g., success, pending, failure
    payment_method = Column(String) # e.g., credit card, paypal
    created_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), nullable=False, onupdate=text('now()'))

    payment_link = relationship('PaymentLink', back_populates="transactions")