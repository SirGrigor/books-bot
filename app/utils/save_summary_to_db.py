from app.database.db_handler import SummaryModel

def save_summary_to_db(db_handler, user_id, summary_type, summary):
	"""
	Saves the summary to the database.
	"""
	try:
		db_handler.save_summary(user_id=user_id, summary_type=summary_type, summary=summary)
	except Exception as e:
		raise RuntimeError(f"Failed to save summary to the database: {e}") from e