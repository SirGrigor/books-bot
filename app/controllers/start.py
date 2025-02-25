# app/controllers/start.py (updated)
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.database.db_handler import save_user_to_db, SessionLocal


class StartController:
	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user = update.effective_user
		username = user.username or user.first_name

		# Log the user data we're about to save
		logging.info(f"Saving user to database: ID={user.id}, Username={user.username}, FirstName={user.first_name}")

		db = SessionLocal()
		try:
			# Attempt to save the user to the database
			db_user = save_user_to_db(db, user.id, user.username, user.first_name)
			logging.info(f"User saved successfully: {db_user}")

			# Create welcome message with explanation of the bot
			welcome_message = (
				f"👋 Welcome, {username}!\n\n"
				"📚 Book Retention Bot 📚\n\n"
				"Most people forget 90% of what they read within weeks. This bot helps you remember key insights from books using AI and spaced repetition.\n\n"
				"Here's how it works:\n"
				"1️⃣ Browse and select books from our categories or add your own\n"
				"2️⃣ Upload the book file (PDF, EPUB, or FB2 format)\n"
				"3️⃣ Get AI-generated chapter summaries\n"
				"4️⃣ Receive spaced repetition reminders to reinforce your learning\n"
				"5️⃣ Test your knowledge with quizzes and teaching moments\n\n"
				"Let's get started! Use /browsebooks to explore our collection or see all commands with /help."
			)

			# Create keyboard with quick actions
			keyboard = [
				[InlineKeyboardButton("📚 Browse Books", callback_data="menu_browse_books")],
				[InlineKeyboardButton("➕ Add New Book", callback_data="menu_add_book")],
				[InlineKeyboardButton("❓ Help", callback_data="menu_help")]
			]
			reply_markup = InlineKeyboardMarkup(keyboard)

			# Send the welcome message without any parsing mode initially
			await update.message.reply_text(welcome_message, reply_markup=reply_markup)
			logging.info(f"Welcome message sent to user {user.id}")

		except Exception as e:
			logging.error(f"Error in start command: {str(e)}")
			# Send a simpler welcome message as a fallback
			await update.message.reply_text(
				f"Welcome {username}! There was a small issue setting up your profile, but you can still use the bot. Try /help to see available commands."
			)
		finally:
			db.close()

	async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Displays a help message with all available commands.
		Updated to include the new book management commands.
		"""
		try:
			help_text = (
				"📚 Book Retention Bot Commands 📚\n\n"
				"Basic Commands:\n"
				"/start - Welcome message and introduction\n"
				"/help - Display this help message\n\n"

				"Book Management:\n"
				"/browsebooks - Browse books by category\n"
				"/searchbooks - Search for books by title or author\n"
				"/addnewbook - Add a new book with details\n"
				"/importbooks - Import multiple books at once\n"
				"/selectbook - Choose from our curated list of books (legacy)\n"
				"/addbook - Add a custom book by title (simple version)\n\n"

				"Learning Features:\n"
				"/viewsummary - View summaries of your selected book's chapters\n"
				"/summary - Summarize any text you send (not related to books)\n"
				"/quiz - Test your knowledge with quiz questions\n"
				"/teach - Practice explaining concepts in your own words\n"
				"/progress - View your reading and retention statistics\n\n"

				"How to Use:\n"
				"1. Browse books with /browsebooks or add your own with /addnewbook\n"
				"2. Upload the book file (PDF, EPUB, FB2) to get detailed chapter summaries\n"
				"3. Use /viewsummary to browse through chapter summaries\n"
				"4. The bot will automatically send you reminders at optimal intervals\n"
				"5. Use /quiz and /teach to actively reinforce your learning\n"
				"6. Track your progress with /progress\n\n"

				"Remember: Active engagement with the material helps retention!"
			)

			await update.message.reply_text(help_text)
		except Exception as e:
			logging.error(f"Error in help command: {str(e)}")
			await update.message.reply_text("Sorry, there was an error displaying the help message.")

	async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles callbacks from the welcome menu
		"""
		try:
			query = update.callback_query
			await query.answer()

			if query.data == "menu_browse_books":
				# Call the browse_books method from BookManagementController
				from app.controllers.book_management import BookManagementController
				book_controller = BookManagementController()
				# Pass the update with the callback query
				await book_controller.browse_books(update, context)

			elif query.data == "menu_add_book":
				# Call the add_new_book method from BookManagementController
				from app.controllers.book_management import BookManagementController
				book_controller = BookManagementController()
				await book_controller.add_new_book(update, context)

			elif query.data == "menu_help":
				# Send help message directly as a response to the callback query
				help_text = (
					"📚 Book Retention Bot Commands 📚\n\n"
					"Basic Commands:\n"
					"/start - Welcome message and introduction\n"
					"/help - Display this help message\n\n"

					"Book Management:\n"
					"/browsebooks - Browse books by category\n"
					"/searchbooks - Search for books by title or author\n"
					"/addnewbook - Add a new book with details\n"
					"/importbooks - Import multiple books at once\n"
					"/selectbook - Choose from our curated list (legacy)\n"
					"/addbook - Add a custom book by title (simple version)\n\n"

					"Learning Features:\n"
					"/viewsummary - View summaries of your selected book's chapters\n"
					"/summary - Summarize any text you send (not related to books)\n"
					"/quiz - Test your knowledge with quiz questions\n"
					"/teach - Practice explaining concepts in your own words\n"
					"/progress - View your reading and retention statistics\n\n"

					"How to Use:\n"
					"1. Browse books with /browsebooks or add your own with /addnewbook\n"
					"2. Upload the book file (PDF, EPUB, FB2) to get detailed chapter summaries\n"
					"3. Use /viewsummary to browse through chapter summaries\n"
					"4. The bot will automatically send you reminders at optimal intervals\n"
					"5. Use /quiz and /teach to actively reinforce your learning\n"
					"6. Track your progress with /progress\n\n"

					"Remember: Active engagement with the material helps retention!"
				)
				await query.edit_message_text(help_text)
		except Exception as e:
			logging.error(f"Error handling menu callback: {str(e)}")
			try:
				await query.edit_message_text(
					"Sorry, there was an error processing your selection. Please try using the command directly.")
			except Exception as inner_e:
				logging.error(f"Failed to send error message: {str(inner_e)}")
