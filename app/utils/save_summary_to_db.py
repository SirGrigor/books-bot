from sqlalchemy.orm import Session
from app.models.summary_model import Summary

def save_summary_to_db(db: Session, user_id: str, original_text: str, summary: str):
	"""
	Saves summary to the database.
	"""
	db_summary = Summary(user_id=user_id, original_text=original_text, summary=summary)
	db.add(db_summary)
	db.commit()
	db.refresh(db_summary)
	return db_summary