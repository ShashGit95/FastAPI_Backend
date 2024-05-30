import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi.background import BackgroundTasks
from schemas import get_settings
from models import User
from dotenv import load_dotenv
from security import hash_password
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, Template


USER_VERIFY_ACCOUNT = "verify-account"
FORGOT_PASSWORD = "password-reset"

load_dotenv()

settings = get_settings()


def send_email(receiver_email, subject, template_name, context):
    
    # Email configuration
    sender_email = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')

    # Connect to SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)

        # Load the Jinja2 template
        file_loader = FileSystemLoader('templates')
        env = Environment(loader=file_loader)
        template = env.get_template(template_name)

        # Render the template with the context data
        html_content = template.render(context)

        # Create message container
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach HTML message to the email
        msg.attach(MIMEText(html_content, 'html'))

        # Send the email
        server.send_message(msg)

# account verification email for creating user
async def send_account_verification_email(user: User, background_tasks: BackgroundTasks):

    # Generate token and activation URL
    string_context = user.get_context_string(context=USER_VERIFY_ACCOUNT)
    token = hash_password(string_context)
    activate_url = f"{settings.FRONTEND_HOST}/auth/account-verify?token={token}"

    # Prepare data for email
    data = {
        'app_name': settings.APP_NAME,
        "name": user.email,
        'activate_url': activate_url
    }
    subject = f"Account Verification - {settings.APP_NAME}"
    html_path = "user/account-verification.html"

    # Await the send_email function and pass background_tasks
    background_tasks.add_task(send_email,user.email, subject, html_path, data)


# account activation confirmation  for activate user
async def send_account_activation_confirmation_email(user: User, background_tasks: BackgroundTasks):
    data = {
        'app_name': settings.APP_NAME,
        "name": user.email,
        'activate_url': f'{settings.FRONTEND_HOST}'
    }
    subject = f"Welcome - {settings.APP_NAME}"
    html_path = "user/account-verification-confirmation.html"

    # Await the send_email function and pass background_tasks
    background_tasks.add_task(send_email,user.email, subject, html_path, data)


 # password reset email        
async def send_password_reset_email(user: User, background_tasks: BackgroundTasks):
    
    string_context = user.get_context_string(context=FORGOT_PASSWORD)
    token = hash_password(string_context)
    reset_url = f"{settings.FRONTEND_HOST}/reset-password?token={token},email={user.email}"
    data = {
        'app_name': settings.APP_NAME,
        "name": user.email,
        'activate_url': reset_url,
    }
    subject = f"Reset Password - {settings.APP_NAME}"
    html_path = "user/password-reset.html"

    # Await the send_email function and pass background_tasks
    background_tasks.add_task(send_email,user.email, subject, html_path, data)

