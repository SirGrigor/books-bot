# app/controllers/book_selection.py - FIXED
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import (
	SessionLocal,
	save_book_selection_to_db,
	get_recommended_books,
	add_custom_book_to_db
)
from app.services.reminders_service import schedule_spaced_repetition

class BookSelectionController:
	async def select_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles /selectbook command - shows a list of curated books to the user
		"""
		db = SessionLocal()
		try:
			# Get the list of recommended books
			books = get_recommended_books(db)

			if not books or len(books) == 0:
				if update.callback_query:
					await update.callback_query.edit_message_text(
						"Sorry, I don't have any recommended books at the moment. "
						"You can add your own book using /addbook."
					)
				else:
					await update.message.reply_text(
						"Sorry, I don't have any recommended books at the moment. "
						"You can add your own book using /addbook."
					)
				return

			# Create an inline keyboard with book options
			keyboard = []
			for book in books:
				keyboard.append([InlineKeyboardButton(book.title, callback_data=f"book_{book.id}")])

			# Add an option to manually enter a book
			keyboard.append([InlineKeyboardButton("Add a different book", callback_data="book_custom")])

			reply_markup = InlineKeyboardMarkup(keyboard)

			message_text = "Choose a book to study using spaced repetition:"

			# Handle the different update contexts (direct command vs callback)
			if update.callback_query:
				await update.callback_query.edit_message_text(
					text=message_text,
					reply_markup=reply_markup
				)
			else:
				await update.message.reply_text(
					text=message_text,
					reply_markup=reply_markup
				)

		except Exception as e:
			logging.error(f"Error in select_book: {str(e)}")
			self._send_error_message(update, "Sorry, there was an error fetching the book list.")
		finally:
			db.close()

	async def handle_book_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the inline keyboard callback when a user selects a book
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("book_") and query.data != "book_custom":
			book_id = int(query.data.split("_")[1])
			user_id = update.effective_user.id

			db = SessionLocal()
			try:
				# Save the book selection
				book = save_book_selection_to_db(db, user_id, book_id)

				# Store book_id in context for reminders
				if not context.chat_data:
					context.chat_data = {}
				context.chat_data["current_book_id"] = book_id

				# Schedule the spaced repetition reminders
				await schedule_spaced_repetition(context, user_id, book.title)

				await query.edit_message_text(
					f"Great choice! You've selected '{book.title}'. "
					f"I'll send you a summary soon, followed by reminders to help you remember the key concepts."
				)

			except Exception as e:
				logging.error(f"Error in handle_book_selection: {str(e)}")
				await query.edit_message_text("Sorry, there was an error processing your selection.")
			finally:
				db.close()

		elif query.data == "book_custom":
			await query.edit_message_text(
				"Please send me the title of the book you want to add. "
				"Just type the title and send it as a message."
			)
			# Store that we're waiting for a book title
			if not context.user_data:
				context.user_data = {}
			context.user_data["awaiting_book_title"] = True

	async def add_custom_book_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handler for the /addbook command
		"""
		await update.message.reply_text(
			"Please send me the title of the book you want to add. "
			"Just type the title and send it as a message."
		)
		# Store that we're waiting for a book title
		if not context.user_data:
			context.user_data = {}
		context.user_data["awaiting_book_title"] = True

	async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles text input based on the current context
		"""
		user_id = update.effective_user.id
		message_text = update.message.text

		# Default user_data if not initialized
		if not hasattr(context, 'user_data') or context.user_data is None:
			context.user_data = {}

		# Check the current context
		if context.user_data.get("awaiting_book_title"):
			# User is adding a custom book
			await self.add_custom_book(update, context)
		elif context.user_data.get("awaiting_quiz_answer"):
			# User is answering a quiz
			# We'll import it at runtime to avoid circular imports
			from app.controllers.quiz import handle_quiz_answer
			await handle_quiz_answer(update, context)
		elif context.user_data.get("awaiting_teaching"):
			# User is providing a teaching explanation
			from app.controllers.teaching import handle_teaching_response
			await handle_teaching_response(update, context)
		else:
			# Default behavior - summarize the text
			from app.controllers.summary_text import summarize_text_command
			await summarize_text_command(update, context)

	async def add_custom_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the addition of a custom book when a user types the title
		"""
		if context.user_data.get("awaiting_book_title"):
			book_title = update.message.text.strip()
			user_id = update.effective_user.id

			db = SessionLocal()
			try:
				# Add the custom book to the database
				book = add_custom_book_to_db(db, book_title, user_id)

				# Store book_id in context for reminders
				if not context.chat_data:
					context.chat_data = {}
				context.chat_data["current_book_id"] = book.id

				# Schedule the spaced repetition reminders
				await schedule_spaced_repetition(context, user_id, book.title)

				# Remove the awaiting flag
				context.user_data.pop("awaiting_book_title")

				await update.message.reply_text(
					f"I've added '{book_title}' to your reading list. "
					f"I'll send you a summary soon, followed by reminders to help you remember the key concepts."
				)

			except Exception as e:
				logging.error(f"Error in add_custom_book: {str(e)}")
				await update.message.reply_text("Sorry, there was an error adding your book.")
			finally:
				db.close()

	def _send_error_message(self, update, text):
		"""Helper method to send error messages in either context"""
		try:
			if update.callback_query:
				update.callback_query.edit_message_text(text)
			else:
				update.message.reply_text(text)
		except Exception as e:
			logging.error(f"Failed to send error message: {str(e)}")