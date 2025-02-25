# app/database/db_handler.py
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from constants.constants import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

def save_summary_to_db(user_id, original_text, summary):
    db = SessionLocal()
    db_summary = Summary(user_id=user_id, original_text=original_text, summary=summary)
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary