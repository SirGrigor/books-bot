import logging
from app.database.db_handler import SessionLocal, initialize_recommended_books

def init_database():
	"""
	Initializes the database with recommended books and ensures required tables exist.
	"""
	logging.info("Initializing database...")

	db = SessionLocal()
	try:
		# Initialize recommended books
		initialize_recommended_books(db)
		logging.info("Database initialization completed")
	except Exception as e:
		logging.error(f"Error during database initialization: {str(e)}")
	finally:
		db.close()

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	init_database()