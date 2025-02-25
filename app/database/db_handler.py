# app/database/db_handler.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from constants.constants import DATABASE_URL

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, unique=True, index=True)  # Telegram user ID
    username = Column(String)  # Telegram username
    first_name = Column(String)  # First name of the user

# Define the Message model
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Telegram user ID
    message_text = Column(Text, nullable=False)  # Content of the message
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

# Define the Summary model
class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Telegram user ID
    title = Column(String)  # Optional title (e.g., chapter name)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)

# Create all tables
Base.metadata.create_all(bind=engine)

# Function to save user metadata
def save_user_to_db(db: SessionLocal, user_id: str, username: str, first_name: str):
    db_user = db.query(User).filter_by(user_id=user_id).first()
    if not db_user:
        db_user = User(user_id=user_id, username=username, first_name=first_name)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user

# Function to save a message
def save_message_to_db(db: SessionLocal, user_id: str, message_text: str):
    db_message = Message(user_id=user_id, message_text=message_text)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Function to save a summary
def save_summary_to_db(db: SessionLocal, user_id: str, title: str, original_text: str, summary: str):
    db_summary = Summary(
        user_id=user_id,
        title=title,
        original_text=original_text,
        summary=summary
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary