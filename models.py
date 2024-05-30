from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from database import Base
from sqlalchemy.sql import func
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    

    # Define the relationship with UserToken
    tokens = relationship("UserToken", back_populates="user")

    
    def get_context_string(self, context: str):
        return f"{context}{self.hashed_password[-6:]}{self.updated_at.strftime('%m%d%Y%H%M%S')}".strip()
        


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey('users.id'))
    access_key = Column(String(250), nullable=True, index=True, default=None)
    refresh_key = Column(String(250), nullable=True, index=True, default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    logout_time = Column(DateTime(timezone=True), nullable=True, server_default=None)
    disabled = Column(Boolean, default=False)  


    # Define the relationship with User
    user = relationship("User", back_populates="tokens")

    # You can add more fields as needed. For example:
    # reset_token = Column(String, index=True, nullable=True)
    # name = Column(String)
    # last_login = Column(DateTime)

    # Add any additional utility methods or relationships here.
    # For example, relationships with other tables (if any).


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id')) # Adjust 'user.id' based on your User model's table name
    video_path = Column(String(255))  # Specify a length, e.g., 255 characters
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")  # Adjust "User" based on your User model's class name