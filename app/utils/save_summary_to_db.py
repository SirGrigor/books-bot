from app.database.db_handler import SummaryModel

def save_summary_to_db(db_handler, user_id, title, summary):
	"""
	Saves a summary to the database.
	"""
	summary_model = SummaryModel(user_id=user_id, title=title, summary=summary)
	db_handler.save_summary(summary_model)