from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SummaryModel(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # Store the Telegram chat_id of the user
    title = Column(String)  # Chapter title or "Short Text"
    summary = Column(Text)  # Generated summary