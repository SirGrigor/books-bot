# app/controllers/quiz.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import SessionLocal, get_user_books, save_quiz_to_db, save_quiz_answer
from app.services.quiz_service import generate_quiz_questions

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
				book = user_book.book
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
				# Get the book summary
				summary = db.query("Summary").filter(
					"Summary.user_id" == user_id,
					"Summary.book_id" == book_id
				).order_by("Summary.created_at.desc()").first()

				if not summary:
					await query.edit_message_text(
						"Sorry, I couldn't find a summary for this book. "
						"Please summarize it first using /summary."
					)
					return

				# Generate quiz questions
				questions = generate_quiz_questions(summary.summary)

				if not questions or len(questions) == 0:
					await query.edit_message_text(
						"Sorry, I couldn't generate quiz questions for this book. "
						"Please try again later."
					)
					return

				# Save the first question to the database
				question = questions[0]
				quiz = save_quiz_to_db(db, user_id, book_id, question["question"], question["answer"])

				# Store the quiz ID in context for answer handling
				context.user_data["awaiting_quiz_answer"] = True
				context.user_data["current_quiz_id"] = quiz.id

				await query.edit_message_text(
					f"Question: {question['question']}\n\n"
					"Reply with your answer, and I'll let you know if it's correct!"
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
		# Get the quiz
		quiz = db.query("Quiz").filter("Quiz.id" == quiz_id).first()

		if not quiz:
			await update.message.reply_text("Sorry, I couldn't find the quiz question.")
			return

		# Simple string comparison for now - could be improved with NLP
		is_correct = user_answer.lower().strip() == quiz.correct_answer.lower().strip()

		# Save the user's answer
		save_quiz_answer(db, quiz_id, user_answer, is_correct)

		# Remove the awaiting flag
		context.user_data.pop("awaiting_quiz_answer", None)
		context.user_data.pop("current_quiz_id", None)

		if is_correct:
			await update.message.reply_text(
				"✅ Correct! Great job!\n\n"
				f"The answer is: {quiz.correct_answer}"
			)
		else:
			await update.message.reply_text(
				"❌ Not quite right.\n\n"
				f"The correct answer is: {quiz.correct_answer}\n\n"
				"Don't worry, spaced repetition will help you remember next time!"
			)

	except Exception as e:
		logging.error(f"Error in handle_quiz_answer: {str(e)}")
		await update.message.reply_text("Sorry, there was an error processing your answer.")
	finally:
		db.close()