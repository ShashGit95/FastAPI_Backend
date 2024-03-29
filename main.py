from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import BackgroundTasks, FastAPI,  status, APIRouter, status, Request, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine
import crud, models, schemas, auth
from auth import get_db, get_current_user, get_current_active_user, retrieve_video
from security import check_user_exist, user_found, user_delete
from user_payment import  payment_intent, webhook_received
from auth import validate_prompt
from user_videos import start_download_video
# from user_payment import checkout_session, create_webhook, portal_session
from dotenv import load_dotenv
import os
import security


load_dotenv()

# create FastAPI app
app = FastAPI()
    
# frontend link
origins = {
    'http://localhost:3000'
}

# connect backend with the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Set to True if your client sends credentials (cookies, etc.)
    allow_methods=["POST"],  # Specify the HTTP methods allowed for CORS requests
    allow_headers=["Content-Type"],  # Specify the allowed request headers
)


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")


# This is for demo purposes!
# Set global state variables
app.state.stripe_customer_id = None
stripe_customer_id = app.state.stripe_customer_id 


# Ensure all database tables are created based on models
models.Base.metadata.create_all(bind=engine)


@app.get("/")
async def health_check():
    return JSONResponse(content={"status": "Hi Cinematic Backend is Running!"})


@app.post("/register", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return await check_user_exist(user, background_tasks, db)


@app.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_account(data: schemas.VerifyUserRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    await auth.activate_user_account(data, db, background_tasks)
    return JSONResponse({"message": "Account is activated successfully."})


@app.post("/token", status_code=status.HTTP_200_OK, response_model=schemas.LoginResponse)
async def user_login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return await auth.get_login_token(data, db)


@app.post("/refresh_token", status_code=status.HTTP_200_OK, response_model=schemas.LoginResponse)
async def refresh_token(refresh_token = Header(), session: Session = Depends(get_db)):
    return await auth.get_refresh_token(refresh_token, session)


@app.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: schemas.EmailRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    await auth.email_forgot_password_link(data, background_tasks, db)
    return JSONResponse({"message": "A email with password reset link has been sent to you."})


@app.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: schemas.ResetRequest, db: Session = Depends(get_db)):
    await auth.reset_user_password(data, db)
    return JSONResponse({"message": "Your password has been updated."})


@app.post("/create-payment-intent", response_model=schemas.PaymentIntentResponse)
async def create_payment_intent():
    return await payment_intent()
    

@app.post("/validate-credit-card", response_model=schemas.CreditCardValidationResponse)
async def validate_credit_card_route(data: schemas.CreditCardValidationRequest):
    return await security.validate_credit_card(data.card_number, data.expiry_date, data.cvv)


@app.get("/payment")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "hasCustomer": app.state.stripe_customer_id is not None})


@app.get('/config')
async def config():
    publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
    return JSONResponse(content={'publishablekey': publishable_key})


@app.get("/success")
async def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/cancel")
async def cancel(request: Request):
    return templates.TemplateResponse("cancel.html", {"request": request})


# @app.post("/create-checkout-session")
# async def create_checkout_session(request: Request):
#     return await checkout_session(request, stripe_customer_id)


# @app.post("/create-portal-session")
# async def create_portal_session():
#     return await portal_session(stripe_customer_id)
    

@app.post("/webhook")
async def webhook_received_method(request: Request):
    # return await create_webhook(request, stripe_signature, webhook_secret)
    return await webhook_received(request)
    

@app.post("/generate_video")
async def process_text_prompt(text_prompt: schemas.TextPrompt, current_user: schemas.UserResponse = Depends(get_current_active_user), db : Session = Depends(get_db)):
    return await validate_prompt(text_prompt, current_user.id, db)


@app.get("/download_video")
async def download_video(video_url: str):
    return await start_download_video(video_url)


@app.get("/user_videos/")
async def list_user_videos(current_user: schemas.UserResponse = Depends(get_current_active_user), db: Session = Depends(get_db)):
   return await retrieve_video(current_user.user_id, db)


@app.post("/logout/")
def logout_user(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_active_user)):
    crud.update_user_logout_time(db, user_id=current_user.id)
    return {"msg": "User logged out successfully."}


@app.get("/me", status_code=status.HTTP_200_OK, response_model=schemas.UserResponse)
async def fetch_user(user = Depends(get_current_user)):
    return user


@app.get("/{pk}", status_code=status.HTTP_200_OK, response_model=schemas.UserResponse)
async def get_user_info(pk, db: Session = Depends(get_db)):
    return await auth.fetch_user_detail(pk, db)


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    return user_found(db_user)


@app.put("/users/{user_id}", response_model=schemas.UserUpdate)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, user_id=user_id, user_update=user)
    return user_found(db_user)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    return user_delete(db_user)
    
