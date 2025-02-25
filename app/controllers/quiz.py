# app/controllers/quiz.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import (
	SessionLocal,
	get_user_books,
	Book,
	Summary,
	save_quiz_to_db,
	save_quiz_answer
)

class QuizController:
	async def send_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the /quiz command
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
					keyboard.append([InlineKeyboardButton(book.title, callback_data=f"quiz_book_{book.id}")])

			reply_markup = InlineKeyboardMarkup(keyboard)

			await update.message.reply_text(
				"Which book would you like to quiz yourself on?",
				reply_markup=reply_markup
			)

		except Exception as e:
			logging.error(f"Error in send_quiz: {str(e)}")
			await update.message.reply_text("Sorry, there was an error preparing the quiz.")
		finally:
			db.close()

	async def handle_book_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the selection of a book for the quiz
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("quiz_book_"):
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

				# Create a simple quiz question
				question = f"What is one key concept you learned from '{book.title}'?"
				answer = "This is a reflective question to test your understanding."

				# Save the question to the database
				quiz = save_quiz_to_db(db, user_id, book_id, question, answer)

				# Store quiz info in context
				if not context.user_data:
					context.user_data = {}
				context.user_data["awaiting_quiz_answer"] = True
				context.user_data["current_quiz_id"] = quiz.id

				await query.edit_message_text(
					f"Question: {question}\n\n"
					"Reply with your answer, and I'll provide feedback on your understanding."
				)

			except Exception as e:
				logging.error(f"Error in handle_book_selection: {str(e)}")
				await query.edit_message_text("Sorry, there was an error generating the quiz.")
			finally:
				db.close()

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles a user's answer to a quiz question
	"""
	if not context.user_data.get("awaiting_quiz_answer"):
		return

	user_answer = update.message.text
	quiz_id = context.user_data.get("current_quiz_id")

	db = SessionLocal()
	try:
		# Since this is a reflective question, all answers are considered correct
		is_correct = True

		# Save the user's answer
		save_quiz_answer(db, quiz_id, user_answer, is_correct)

		# Remove the awaiting flag
		context.user_data.pop("awaiting_quiz_answer", None)
		context.user_data.pop("current_quiz_id", None)

		await update.message.reply_text(
			"Thank you for your answer! Reflecting on what you've learned helps reinforce your understanding.\n\n"
			"I'll continue to send you quiz questions at optimal intervals to help you retain this knowledge."
		)

	except Exception as e:
		logging.error(f"Error in handle_quiz_answer: {str(e)}")
		await update.message.reply_text("Sorry, there was an error processing your answer.")
	finally:
		db.close()