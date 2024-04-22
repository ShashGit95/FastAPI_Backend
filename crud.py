from datetime import datetime
from sqlalchemy.orm import Session
import models, schemas
from security import hash_password
from user_email import send_account_verification_email



# Retrieve a user by id.
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


# Retrieve a user by email.
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


#Add a new user to the database.
async def create_user(db, user, background_tasks):

    hashed_password = hash_password(user.password)

    # Ensure the username is included here
    db_user = models.User(email=user.email, hashed_password=hashed_password, is_active = False, updated_at = datetime.utcnow())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Account Verification Email
    await send_account_verification_email(db_user, background_tasks=background_tasks)
    return db_user


# Update an existing user's details.
def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    for var, value in vars(user_update).items():
        setattr(db_user, var, value) if value else None
    db.commit()
    db.refresh(db_user)
    return db_user


# Delete a user from the database.
def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


# update user logout time
def update_user_logout_time(db: Session, user_id: int):
    # Fetch the user token record from the database
    user_token = db.query(models.UserToken).filter(models.UserToken.user_id == user_id).first()

    if user_token:
        # Update the logout time for the user
        user_token.logout_time = datetime.now()

        # Commit the changes to the database
        db.commit()

        print("Logout time updated successfully.")
    else:
        print("User token not found.")

