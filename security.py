import logging  # Import the logging module for logging messages
import secrets  # Import the secrets module for generating secure tokens
import base64 # Import the base64 module for encoding and decoding strings
from fastapi import HTTPException   
from sqlalchemy.orm import Session  # Import Session from sqlalchemy.orm for database session management
from passlib.context import CryptContext  # Import CryptContext from passlib.context for password hashing
from datetime import datetime
from schemas import CreditCardValidationResponse
from fastapi.security import OAuth2PasswordBearer
import crud  


# Initialize the CryptContext object for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password):
    return pwd_context.hash(password)


# Verify a hashed password against one provided by user
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Hash a password for storing.
def get_password_hash(password):
    return pwd_context.hash(password)


# Generate a unique string of specified length
def unique_string(byte: int = 8) -> str:
    return secrets.token_urlsafe(byte)


# Authenticate user by email and password.
def authenticate_user(db: Session, name: str, password: str):
    user = crud.get_user_by_username(db, name)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# check user by email and user name
async def check_user_exist(user,background_tasks, db):

    # Check if the email is already registered
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if the username is already taken
    # db_user_by_username = crud.get_user_by_username(db, username=user.username)
    # if db_user_by_username:
    #     raise HTTPException(status_code=400, detail="Username already taken")
    
    return await crud.create_user(db=db, user=user, background_tasks=background_tasks)


# check user is found
def user_found(user):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# check user deleted successfully
def user_delete(user):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}


# Encode a string using base85 encoding
def str_encode(string: str) -> str:
    return base64.b85encode(string.encode('ascii')).decode('ascii')


# Decode a string using base85 decoding
def str_decode(string: str) -> str:
    return base64.b85decode(string.encode('ascii')).decode('ascii')


# Load a user from the database by username
async def load_user(email: str, db):
    from models import User
    try:
        user = db.query(User).filter(User.email == email).first()
    except Exception as user_exec:
        logging.info(f"User Not Found, Email: {User.email}")
        user = None
    return user


#creditcard validation
async def validate_credit_card(card_number: str, expiry: str, cvv: str):
    # validate credit card number
    sum_odd_digits = 0
    sum_even_digits = 0
    total = 0

    # replace spaces and '-'
    card_number = card_number.replace("-","")
    card_number = card_number.replace(" ","")
    card_number= card_number[::-1]

    for x in card_number[::2]:
        sum_odd_digits += int(x)

    for x in card_number[1::2] :
        x = int(x) * 2
        if x >= 10:
            sum_even_digits += (1+(x%10))
        else:
            sum_even_digits += x

    total = sum_odd_digits + sum_even_digits

    if total % 10 != 0 :
        return CreditCardValidationResponse(valid=False, message="Invalid credit card number")
    
    # validate credit card expiration date
    try:
        expiry_date = datetime.strptime(expiry, '%m/%y')
        if expiry_date < datetime.now():
            return CreditCardValidationResponse(valid=False, message="Credit card has expired")
    except ValueError:
        return CreditCardValidationResponse(valid=False, message="Invalid expiration date format. Please use MM/YY format")

    # Validate CVV format (assuming 3 or 4 digits)
    if not (cvv.isdigit() and len(cvv) in [3, 4]):
        return CreditCardValidationResponse(valid=False, message="Invalid CVV format. CVV should be a 3 or 4 digit number")

    return CreditCardValidationResponse(valid=True, message="Credit card is valid")
