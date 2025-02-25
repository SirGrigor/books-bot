# app/controllers/teaching.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import SessionLocal, get_user_books, Book, Summary

class TeachingController:
	def __init__(self, teaching_service):
		self.teaching_service = teaching_service

	async def send_teaching_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, summary=None):
		"""
		Sends a teaching prompt to help the user solidify their understanding.
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

			# Create an inline keyboard with book options
			keyboard = []
			for user_book in user_books:
				# Get the book for this user_book
				book = db.query(Book).filter(Book.id == user_book.book_id).first()
				if book:
					keyboard.append([InlineKeyboardButton(book.title, callback_data=f"teach_book_{book.id}")])

			reply_markup = InlineKeyboardMarkup(keyboard)

			await update.message.reply_text(
				"Teaching is one of the best ways to learn! Choose a book to practice explaining:",
				reply_markup=reply_markup
			)

		except Exception as e:
			logging.error(f"Error in send_teaching_prompt: {str(e)}")
			await update.message.reply_text("Sorry, there was an error preparing the teaching prompt.")
		finally:
			db.close()

	async def handle_book_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the selection of a book for teaching
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("teach_book_"):
			book_id = int(query.data.split("_")[2])
			user_id = update.effective_user.id

			db = SessionLocal()
			try:
				# Get the book
				book = db.query(Book).filter(Book.id == book_id).first()
				if not book:
					await query.edit_message_text("Sorry, I couldn't find this book.")
					return

				# Get the summary for this book
				summary = db.query(Summary).filter(
					Summary.user_id == str(user_id),
					Summary.book_id == book_id
				).order_by(Summary.id.desc()).first()

				if not summary:
					await query.edit_message_text(
						f"I don't have a summary for '{book.title}' yet. "
						f"Try uploading a summary first!"
					)
					return

				# Generate a teaching prompt
				teaching_prompt = f"Explain one key concept from '{book.title}' as if you were teaching it to someone who has never heard of it before."

				# Store that we're waiting for a teaching response
				if not context.user_data:
					context.user_data = {}
				context.user_data["awaiting_teaching"] = True
				context.user_data["teaching_book_id"] = book_id

				await query.edit_message_text(
					f"👨‍🏫 Teaching Challenge for '{book.title}'\n\n"
					"Explaining concepts in your own words is one of the best ways to ensure you understand and remember them.\n\n"
					f"{teaching_prompt}\n\n"
					"Reply with your explanation, and I'll provide feedback!"
				)

			except Exception as e:
				logging.error(f"Error in handle_book_selection: {str(e)}")
				await query.edit_message_text("Sorry, there was an error generating the teaching prompt.")
			finally:
				db.close()

async def handle_teaching_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles the user's response to a teaching prompt
	"""
	if not context.user_data.get("awaiting_teaching"):
		return

	user_response = update.message.text
	book_id = context.user_data.get("teaching_book_id")

	# Remove the awaiting flag
	context.user_data.pop("awaiting_teaching", None)
	context.user_data.pop("teaching_book_id", None)

	db = SessionLocal()
	try:
		# Get the book
		book = db.query(Book).filter(Book.id == book_id).first()
		book_title = book.title if book else "the book"

		# Provide feedback
		feedback = (
			"Thank you for your explanation! Teaching is one of the best ways to reinforce your learning.\n\n"
			f"Your explanation of the concept from {book_title} shows your understanding. "
			"Continue to practice explaining these ideas in your own words to strengthen your retention."
		)

		await update.message.reply_text(feedback)

	except Exception as e:
		logging.error(f"Error handling teaching response: {str(e)}")
		await update.message.reply_text(
			"Thank you for your explanation! Teaching others is one of the best ways to learn."
		)
	finally:
		db.close()