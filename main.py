# main.py (updated with fixed imports and command routing)
import logging

from telegram import Update
from telegram.ext import (
	ApplicationBuilder,
	CommandHandler,
	MessageHandler,
	filters,
	CallbackQueryHandler,
	ContextTypes
)

from app.controllers.book_management import BookManagementController
from app.controllers.book_selection import BookSelectionController
from app.controllers.progress import ProgressController
from app.controllers.quiz import QuizController
from app.controllers.start import StartController
from app.controllers.summary_book import summarize_book_command
from app.controllers.summary_text import summarize_text_command
from app.controllers.summary_view import view_book_summary_command, handle_summary_selection
from app.controllers.teaching import TeachingController
from app.database.db_handler import create_tables
from app.database.init_db import init_database
from app.services.reminders_service import process_due_reminders
from app.services.teaching_service import generate_discussion_prompt
from app.utils.logging_config import configure_logging
from constants.constants import TELEGRAM_BOT_TOKEN

# Configure logging
configure_logging()

logging.info("Starting bot...")


def main():
	# Force create all tables first
	try:
		create_tables()
	except Exception as e:
		logging.error(f"Error creating tables: {str(e)}")

	# Initialize the database
	try:
		init_database()
	except Exception as e:
		logging.error(f"Error initializing database: {str(e)}")
	# Continue anyway, as the basic functionality should still work

	# Check if token is available
	if not TELEGRAM_BOT_TOKEN:
		logging.error("Telegram bot token not found! Please set the TELEGRAM_BOT_TOKEN environment variable.")
		return

	# Initialize the bot
	logging.info(f"Building application with token: {TELEGRAM_BOT_TOKEN[:5]}...")
	application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
	logging.info("Application built successfully!")

	# Initialize controllers
	start_controller = StartController()
	book_selection_controller = BookSelectionController()
	book_management_controller = BookManagementController()
	quiz_controller = QuizController()
	teaching_service = generate_discussion_prompt
	teaching_controller = TeachingController(teaching_service)
	progress_controller = ProgressController()

	# Add command handlers - ORDER IS IMPORTANT
	logging.info("Adding command handlers...")

	# Basic commands
	application.add_handler(CommandHandler("start", start_controller.start))
	application.add_handler(CommandHandler("help", start_controller.help))

	# Book management commands - these should be processed BEFORE any callback handlers
	application.add_handler(CommandHandler("browsebooks", book_management_controller.browse_books))
	application.add_handler(CommandHandler("searchbooks", book_management_controller.search_books))
	application.add_handler(CommandHandler("addnewbook", book_management_controller.add_new_book))
	application.add_handler(CommandHandler("importbooks", book_management_controller.handle_import_books))
	application.add_handler(CommandHandler("selectbook", book_selection_controller.select_book))
	application.add_handler(CommandHandler("addbook", book_selection_controller.add_custom_book_command))

	# Learning feature commands
	application.add_handler(CommandHandler("summary", summarize_text_command))
	application.add_handler(CommandHandler("viewsummary", view_book_summary_command))
	application.add_handler(CommandHandler("quiz", quiz_controller.send_quiz))
	application.add_handler(CommandHandler("teach", teaching_controller.send_teaching_prompt))
	application.add_handler(CommandHandler("progress", progress_controller.show_progress))

	# Add callback query handlers - these should come AFTER command handlers
	logging.info("Adding callback query handlers...")
	application.add_handler(CallbackQueryHandler(start_controller.handle_menu_callback, pattern=r"^menu_"))
	application.add_handler(CallbackQueryHandler(book_selection_controller.handle_book_selection, pattern=r"^book_"))

	# Book management callback handlers
	application.add_handler(
		CallbackQueryHandler(book_management_controller.handle_category_selection, pattern=r"^category_"))
	application.add_handler(CallbackQueryHandler(book_management_controller.handle_pagination, pattern=r"^page_"))
	application.add_handler(CallbackQueryHandler(book_management_controller.search_books, pattern=r"^search_books$"))
	application.add_handler(CallbackQueryHandler(book_management_controller.add_new_book, pattern=r"^add_new_book$"))
	application.add_handler(
		CallbackQueryHandler(book_management_controller.handle_import_books, pattern=r"^import_books$"))
	application.add_handler(CallbackQueryHandler(book_management_controller.handle_navigation,
												 pattern=r"^(back_to_categories|add_book_to_|add_book_title_)"))

	# Learning feature callback handlers
	application.add_handler(CallbackQueryHandler(quiz_controller.handle_book_selection, pattern=r"^quiz_book_"))
	application.add_handler(CallbackQueryHandler(teaching_controller.handle_book_selection, pattern=r"^teach_book_"))
	application.add_handler(CallbackQueryHandler(progress_controller.mark_book_completed, pattern=r"^complete_book_"))
	application.add_handler(CallbackQueryHandler(handle_summary_selection, pattern=r"^summary_"))

	# Add message handlers
	logging.info("Adding message handlers...")

	# Update message handler to route text input based on context
	async def route_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""Route text input to the appropriate handler based on context"""
		if not context.user_data:
			context.user_data = {}

		if context.user_data.get("awaiting_book_title"):
			# Original book addition flow
			await book_selection_controller.handle_text_input(update, context)
		elif context.user_data.get("awaiting_book_details"):
			# New detailed book addition
			await book_management_controller.handle_book_details(update, context)
		elif context.user_data.get("awaiting_book_import"):
			# Book import list
			await book_management_controller.handle_book_import(update, context)
		elif context.user_data.get("awaiting_search_query"):
			# Book search query
			await book_management_controller.handle_search_query(update, context)
		elif context.user_data.get("awaiting_quiz_answer"):
			# User is answering a quiz
			from app.controllers.quiz import handle_quiz_answer
			await handle_quiz_answer(update, context)
		elif context.user_data.get("awaiting_teaching"):
			# User is providing a teaching explanation
			from app.controllers.teaching import handle_teaching_response
			await handle_teaching_response(update, context)
		else:
			# Default behavior - summarize the text
			await summarize_text_command(update, context)

	application.add_handler(MessageHandler(
		filters.TEXT & ~filters.COMMAND,
		route_text_input
	))

	application.add_handler(MessageHandler(filters.Document.ALL, summarize_book_command))

	# Schedule the reminder job - run every hour
	logging.info("Setting up job queue...")
	application.job_queue.run_repeating(process_due_reminders, interval=3600, first=60)

	# Start polling - this will keep the application running
	logging.info("Starting to poll for updates. Bot is now running!")
	application.run_polling(poll_interval=1.0, timeout=30)

	# This code should never be reached while the bot is running properly
	logging.info("Bot has stopped running.")


if __name__ == "__main__":
	main()
