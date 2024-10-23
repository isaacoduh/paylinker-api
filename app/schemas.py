from certifi import contents
from pydantic import BaseModel, EmailStr, conint, ConfigDict
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
