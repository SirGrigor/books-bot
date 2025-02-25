# migrations.py
import os
import logging
import sqlite3
from constants.constants import DATABASE_URL

# Extract the database path from the URL
db_path = DATABASE_URL.replace('sqlite:///', '')

def run_migrations():
	"""
	Safely adds new tables and columns to the existing database.
	"""
	logging.info("Running database migrations...")

	# Connect to the database
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	# Check if the users table exists and add columns if needed
	cursor.execute("PRAGMA table_info(users)")
	columns = [column[1] for column in cursor.fetchall()]

	try:
		# Add created_at column to users table if it doesn't exist
		if 'created_at' not in columns:
			cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
			logging.info("Added created_at column to users table")

		# Create books table if it doesn't exist
		cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            description TEXT,
            is_recommended BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
		logging.info("Created or verified books table")

		# Create user_books table if it doesn't exist
		cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            retention_score REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """)
		logging.info("Created or verified user_books table")

		# Create reminders table if it doesn't exist
		cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_book_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            scheduled_for TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT 0,
            sent_at TIMESTAMP,
            FOREIGN KEY (user_book_id) REFERENCES user_books (id)
        )
        """)
		logging.info("Created or verified reminders table")

		# Create quizzes table if it doesn't exist
		cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            user_answer TEXT,
            is_correct BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            answered_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """)
		logging.info("Created or verified quizzes table")

		# Initialize recommended books if the books table is empty
		cursor.execute("SELECT COUNT(*) FROM books WHERE is_recommended = 1")
		recommended_count = cursor.fetchone()[0]

		if recommended_count == 0:
			# Insert recommended books
			recommended_books = [
				("Atomic Habits", "James Clear", "An easy and proven way to build good habits and break bad ones."),
				("Sapiens", "Yuval Noah Harari", "A brief history of humankind."),
				("The Psychology of Money", "Morgan Housel", "Timeless lessons on wealth, greed, and happiness."),
				("Thinking, Fast and Slow", "Daniel Kahneman", "How two systems drive the way we think and make choices."),
				("Deep Work", "Cal Newport", "Rules for focused success in a distracted world.")
			]

			cursor.executemany(
				"INSERT INTO books (title, author, description, is_recommended) VALUES (?, ?, ?, 1)",
				recommended_books
			)
			logging.info(f"Added {len(recommended_books)} recommended books")

		# Commit the changes
		conn.commit()
		logging.info("Database migrations completed successfully")

	except Exception as e:
		# Roll back any changes if something goes wrong
		conn.rollback()
		logging.error(f"Error during migrations: {str(e)}")
		raise
	finally:
		# Close the connection
		conn.close()

if __name__ == "__main__":
	# Configure logging
	logging.basicConfig(level=logging.INFO)
	run_migrations()