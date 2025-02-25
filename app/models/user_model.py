# app/models/user_model.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String, nullable=False, unique=True, index=True)  # Telegram user ID
	username = Column(String)  # Telegram username
	first_name = Column(String)  # First name of the user