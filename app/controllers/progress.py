# app/controllers/progress.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database.db_handler import SessionLocal, get_user_books, get_user_progress

class ProgressController:
	async def show_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the /progress command - shows the user's reading progress
		"""
		user_id = update.effective_user.id

		db = SessionLocal()
		try:
			# Get the user's books
			user_books = get_user_books(db, user_id)

			if not user_books or len(user_books) == 0:
				await update.message.reply_text(
					"You don't have any books in your reading list yet. "
					"Use /selectbook to choose a book or /addbook to add a custom one."
				)
				return

			# Build the progress report
			progress_report = "📚 Your Reading Progress 📚\n\n"

			for user_book in user_books:
				book = user_book.book

				# Get the user's progress for this book
				progress = get_user_progress(db, user_id, book.id)

				if progress:
					status = "✅ Completed" if progress.completed else "📖 In Progress"
					retention = f"{progress.retention_score:.1f}%" if progress.retention_score > 0 else "Not measured yet"

					progress_report += f"*{book.title}*\n"
					if book.author:
						progress_report += f"by {book.author}\n"
					progress_report += f"Status: {status}\n"
					progress_report += f"Retention Score: {retention}\n"
					progress_report += f"Started: {progress.started_at.strftime('%Y-%m-%d')}\n"

					if progress.completed:
						completed_date = progress.completed_at.strftime('%Y-%m-%d')
						progress_report += f"Completed: {completed_date}\n"

					progress_report += "\n"

			# Add some encouragement
			progress_report += "Keep up the great work! Regular reviews will help you retain what you've learned. 🧠"

			await update.message.reply_text(progress_report, parse_mode='Markdown')

		except Exception as e:
			logging.error(f"Error in show_progress: {str(e)}")
			await update.message.reply_text("Sorry, there was an error retrieving your progress.")
		finally:
			db.close()

	async def mark_book_completed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Marks a book as completed
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("complete_book_"):
			book_id = int(query.data.split("_")[2])
			user_id = update.effective_user.id

			db = SessionLocal()
			try:
				# Get the user-book relationship
				user_book = db.query("UserBook").filter(
					"UserBook.user_id" == user_id,
					"UserBook.book_id" == book_id
				).first()

				if not user_book:
					await query.edit_message_text("Sorry, I couldn't find this book in your reading list.")
					return

				# Mark as completed
				user_book.completed = True
				user_book.completed_at = datetime.utcnow()
				db.commit()

				# Get the book title
				book = db.query("Book").filter("Book.id" == book_id).first()

				await query.edit_message_text(
					f"🎉 Congratulations on completing '{book.title}'! 🎉\n\n"
					"I'll continue to send you spaced repetition reminders to help you retain what you've learned."
				)

			except Exception as e:
				logging.error(f"Error in mark_book_completed: {str(e)}")
				await query.edit_message_text("Sorry, there was an error marking the book as completed.")
			finally:
				db.close()