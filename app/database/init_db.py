# app/database/init_db.py
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database.db_handler import SessionLocal, initialize_recommended_books, create_tables

def init_database():
	"""
	Initializes the database with recommended books and ensures required tables exist.
	"""
	logging.info("Initializing database...")

	try:
		# First ensure tables exist
		create_tables()

		# Then initialize with recommended books
		db = SessionLocal()
		try:
			initialize_recommended_books(db)
			logging.info("Database initialization completed")
		except Exception as e:
			logging.error(f"Error during database initialization: {str(e)}")
		finally:
			db.close()
	except Exception as e:
		logging.error(f"Failed to initialize database: {str(e)}")

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	init_database()