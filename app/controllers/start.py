# app/controllers/start.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import save_user_to_db, SessionLocal


class StartController:
	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user = update.effective_user
		username = user.username or user.first_name
		db = SessionLocal()  # Use SessionLocal instead of Session

		try:
			save_user_to_db(db, user.id, user.username, user.first_name)

			# Create welcome message with explanation of the bot
			welcome_message = (
				f"👋 Welcome, {username}!\n\n"
				"📚 *Book Retention Bot* 📚\n\n"
				"Most people forget 90% of what they read within weeks. This bot helps you remember key insights from books using AI and spaced repetition.\n\n"
				"*Here's how it works:*\n"
				"1️⃣ Pick a book from our curated list or add your own\n"
				"2️⃣ Get an AI-generated summary of the key insights\n"
				"3️⃣ Receive spaced repetition reminders to reinforce your learning\n"
				"4️⃣ Test your knowledge with quizzes and teaching moments\n"
				"5️⃣ Track your retention progress over time\n\n"
				"Let's get started! Use /selectbook to choose a book or see all commands with /help."
			)

			# Create keyboard with quick actions
			keyboard = [
				[InlineKeyboardButton("📚 Select a Book", callback_data="menu_select_book")],
				[InlineKeyboardButton("❓ Help", callback_data="menu_help")]
			]
			reply_markup = InlineKeyboardMarkup(keyboard)

			await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

		except Exception as e:
			logging.error(f"Error in start command: {str(e)}")
			await update.message.reply_text(f"Welcome! There was a small issue setting up your profile, but you can still use the bot. Try /help to see available commands.")
		finally:
			db.close()

	async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Displays a help message with all available commands.
		"""
		try:
			help_text = (
				"📚 *Book Retention Bot Commands* 📚\n\n"
				"*Basic Commands:*\n"
				"/start - Welcome message and introduction\n"
				"/help - Display this help message\n\n"

				"*Book Selection:*\n"
				"/selectbook - Choose from our curated list of books\n"
				"/addbook - Add a custom book by title\n\n"

				"*Learning Features:*\n"
				"/summary - Get or view a book summary\n"
				"/quiz - Test your knowledge with quiz questions\n"
				"/teach - Practice explaining concepts in your own words\n"
				"/progress - View your reading and retention statistics\n\n"

				"*How to Use:*\n"
				"1. Start by selecting a book with /selectbook\n"
				"2. Read the AI-generated summary\n"
				"3. The bot will automatically send you reminders at optimal intervals\n"
				"4. Use /quiz and /teach to actively reinforce your learning\n"
				"5. Track your progress with /progress\n\n"

				"Remember: Active engagement with the material helps retention!"
			)

			await update.message.reply_text(help_text, parse_mode='Markdown')
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

			if query.data == "menu_select_book":
				# Call the select_book method from BookSelectionController
				from app.controllers.book_selection import BookSelectionController
				book_controller = BookSelectionController()
				await book_controller.select_book(update, context)
			elif query.data == "menu_help":
				await self.help(update, context)
		except Exception as e:
			logging.error(f"Error handling menu callback: {str(e)}")
			await update.callback_query.edit_message_text("Sorry, there was an error processing your selection. Please try using the command directly.")