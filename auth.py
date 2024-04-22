from datetime import datetime, timedelta
import logging
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import joinedload, Session
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User  
from security import verify_password, unique_string, str_encode, str_decode, load_user, hash_password
from schemas import TokenData
from fastapi import Depends, HTTPException, status, APIRouter
from database import SessionLocal
from models import User, UserToken, Video
from user_email import send_account_activation_confirmation_email, send_password_reset_email
import os
from user_email import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD
from user_videos import create_video
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix = '/auth',
    tags = ['auth']
)


# Configuration
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ["REFRESH_TOKEN_EXPIRE_MINUTES"])


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]



# decode and validate an access token.
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user ID")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


# Dependency to get the current user from a token
# def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#     user = db.query(User).filter(username=token_data.username).first()
#     if user is None:
#         raise credentials_exception
#     return user


# Get current user from a token    
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = await get_token_user(token=token, db=db)
    if user:
        return user
    raise HTTPException(status_code=401, detail="Not authorised.")


# Fetch user details
async def fetch_user_detail(pk, session):
    user = session.query(User).filter(User.id == pk).first()
    if user:
        return user
    raise HTTPException(status_code=400, detail="User does not exists.")


# get current active user
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# activate user account
async def activate_user_account(data, db, background_tasks):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="This link is not valid.")
    
    user_token = user.get_context_string(context= USER_VERIFY_ACCOUNT)
    try:
        token_valid = verify_password(user_token, data.token)
    except Exception as verify_exec:
        logging.exception(verify_exec)
        token_valid = False
    if not token_valid:
        raise HTTPException(status_code=400, detail="This link either expired or not valid.")
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    user.verified_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)

    # Activation confirmation email
    await send_account_activation_confirmation_email(user, background_tasks)
    return user


# sending forgot password email
async def email_forgot_password_link(data, background_tasks, session):
    user = await load_user(data.email, session)
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="Your account is not verified. Please check your email inbox to verify your account.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Your account has been dactivated. Please contact support.")
    
    await send_password_reset_email(user, background_tasks)


# resetting the password
async def reset_user_password(data, session):
    user = await load_user(data.email, session)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")
        
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    user_token = user.get_context_string(context=FORGOT_PASSWORD)
    try:
        token_valid = verify_password(user_token, data.token)
    except Exception as verify_exec:
        logging.exception(verify_exec)
        token_valid = False
    if not token_valid:
        raise HTTPException(status_code=400, detail="Invalid window.")
    
    user.password = hash_password(data.password)
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    # Notify user that password has been updated


# Get token payload
def get_token_payload(token: str, secret: str, algo: str):
    try:
        payload = jwt.decode(token, secret, algorithms=algo)
    except Exception as jwt_exec:
        logging.debug(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload


# Generate token
def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    return jwt.encode(payload, secret, algorithm=algo)


# Get token for the user
async def get_token_user(token: str, db):
    payload = get_token_payload(token, SECRET_KEY, ALGORITHM)
    if payload:
        user_token_id = str_decode(payload.get('r'))
        user_id = str_decode(payload.get('sub'))
        access_key = payload.get('a')
        user_token = db.query(UserToken).options(joinedload(UserToken.user)).filter(UserToken.access_key == access_key,
                                                 UserToken.id == user_token_id,
                                                 UserToken.user_id == user_id,
                                                 UserToken.expires_at > datetime.utcnow()
                                                 ).first()
        if user_token:
            return user_token.user
    return None


# Get refresh token
async def get_refresh_token(refresh_token, session):
    token_payload = get_token_payload(refresh_token, SECRET_KEY, ALGORITHM)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    refresh_key = token_payload.get('t')
    access_key = token_payload.get('a')
    user_id = str_decode(token_payload.get('sub'))
    user_token = session.query(UserToken).options(joinedload(UserToken.user)).filter(UserToken.refresh_key == refresh_key,
                                                 UserToken.access_key == access_key,
                                                 UserToken.user_id == user_id,
                                                 UserToken.expires_at > datetime.utcnow()
                                                 ).first()
    if not user_token:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_token.expires_at = datetime.utcnow()
    session.add(user_token)
    session.commit()
    return _generate_tokens(user_token.user, session)


# Generate access and refresh tokens
def _generate_tokens(user, session):
    refresh_key = unique_string(100)
    access_key = unique_string(50)
    rt_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    user_token = UserToken()
    user_token.user_id = user.id
    user_token.refresh_key = refresh_key
    user_token.access_key = access_key
    user_token.expires_at = datetime.utcnow() + rt_expires
    session.add(user_token)
    session.commit()
    session.refresh(user_token)

    at_payload = {
        "sub": str_encode(str(user.id)),
        'a': access_key,
        'r': str_encode(str(user_token.id)),
        'n': str_encode(f"{user.email}")
    }

    at_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = generate_token(at_payload, SECRET_KEY, ALGORITHM, at_expires)

    rt_payload = {"sub": str_encode(str(user.id)), "t": refresh_key, 'a': access_key}
    refresh_token = generate_token(rt_payload, SECRET_KEY, ALGORITHM, rt_expires)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": at_expires.seconds
    }
    

# verify the email and password
# Verify that user account is verified
# Verify user account is active
# generate access_token and refresh_token and ttl

async def get_login_token(data, db): 
    user = await load_user(data.username, db)
    if not user:
        raise HTTPException(status_code=400, detail="Email is not registered with us.")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    
    # if not user.verified_at:
    #     raise HTTPException(status_code=400, detail="Your account is not verified. Please check your email inbox to verify your account.")
    
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Your account has been dactivated. Please contact support.")
        
    # Generate the JWT Token
    return _generate_tokens(user, db)


# text prompt validation to generate videos
async def validate_prompt(text_prompt: str, user_id: int, db):

    output_folder_path = 'static/output_video'

    if not text_prompt.text:
        raise HTTPException(status_code=400, detail="Text prompt is missing or empty.")
    
    prompt = text_prompt.text
    print(f'Text Prompt: {prompt}')

    # Perform video generation based on the text prompt
    # Assuming create_video function is defined elsewhere
    video_path = await create_video(prompt, user_id, db)
    
    # Placeholder logic for demonstration
    generated_video_url = os.path.join(output_folder_path, os.path.basename(video_path))
    return {"video_url": generated_video_url}


# retrive videos from user id
async def retrieve_video(user_id: int, db: Session):

    videos = db.query(Video).filter(Video.user_id == user_id).all()
    # Extract the video paths
    video_paths = [video.video_path for video in videos]
    
    return video_paths

