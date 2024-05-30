from pathlib import Path
from typing import Optional
from typing import Union
from datetime import datetime
from pydantic import EmailStr, BaseModel
from base import BaseResponse
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from functools import lru_cache

# Load variables from .env file into the environment
load_dotenv()


class Settings(BaseSettings):

    # App
    APP_NAME: str = os.environ.get("APP_NAME")
    DEBUG: bool = bool(os.environ.get("DEBUG", False))
    
    # FrontEnd Application
    FRONTEND_HOST: str = os.environ.get("FRONTEND_HOST", "http://localhost:3000")



# Schema for User Creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str 
    # username: str  


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    username: str | None = None


class TextPrompt(BaseModel):
    text: str


class UserResponse(BaseResponse):
    id: int
    email: EmailStr
    is_active: bool
    created_at: Union[str, None, datetime] = None
    # username: str

    
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"

   
class VerifyUserRequest(BaseModel):
    token: str
    email: EmailStr


class ResetRequest(BaseModel):
    token: str
    email: EmailStr
    password: str


class CreditCardValidationRequest(BaseModel):
    card_number: str
    expiry_date: str
    cvv: str


class EmailRequest(BaseModel):
    email: EmailStr


# To check payment intent end point from passing values
class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str  



class CreditCardValidationResponse(BaseModel):
    valid: bool
    message: str


class PaymentResponse(BaseModel):
    message: str


class PaymentIntentResponse(BaseModel):
    clientSecret: str


# User Base Schema
class UserBase(BaseModel):
    email: EmailStr


# Schema for reading user data
class UserRead(UserBase):
    id: int
    is_active: bool = True
    # Include additional fields from your User model as needed

    class Config:
        from_attributes = True

# Schema for updating user data
class UserUpdate(BaseModel):
    email: EmailStr = None
    password: str = None  # Include password field for updating
    is_active: bool = None
    # You can include fields for other user attributes

    class Config:
        from_attributes = True

# Login Form Schema
class LoginForm(BaseModel):
    username: str
    password: str


class UserResponseModel(BaseModel):
    # Other fields...
    disabled: bool  # Ensure this matches the structure you're returning


@lru_cache()
def get_settings() -> Settings:
    return Settings()
