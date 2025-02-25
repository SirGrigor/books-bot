# main.py - FIXED
import logging
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from app.controllers.start import StartController
from app.controllers.summary_text import summarize_text_command
from app.controllers.summary_book import summarize_book_command
from app.controllers.book_selection import BookSelectionController
from app.controllers.quiz import QuizController
from app.controllers.teaching import TeachingController
from app.controllers.progress import ProgressController
from app.services.teaching_service import generate_discussion_prompt
from app.services.reminders_service import process_due_reminders
from app.utils.logging_config import configure_logging
from app.database.init_db import init_database
from app.database.db_handler import create_tables
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
	quiz_controller = QuizController()
	teaching_service = generate_discussion_prompt  # Pass the function
	teaching_controller = TeachingController(teaching_service)
	progress_controller = ProgressController()

	# Add command handlers
	logging.info("Adding command handlers...")
	application.add_handler(CommandHandler("start", start_controller.start))
	application.add_handler(CommandHandler("help", start_controller.help))
	application.add_handler(CommandHandler("selectbook", book_selection_controller.select_book))
	application.add_handler(CommandHandler("addbook", book_selection_controller.add_custom_book_command))
	application.add_handler(CommandHandler("summary", summarize_text_command))
	application.add_handler(CommandHandler("quiz", quiz_controller.send_quiz))
	application.add_handler(CommandHandler("teach", teaching_controller.send_teaching_prompt))
	application.add_handler(CommandHandler("progress", progress_controller.show_progress))

	# Add callback query handlers
	logging.info("Adding callback query handlers...")
	application.add_handler(CallbackQueryHandler(start_controller.handle_menu_callback, pattern=r"^menu_"))
	application.add_handler(CallbackQueryHandler(book_selection_controller.handle_book_selection, pattern=r"^book_"))
	application.add_handler(CallbackQueryHandler(quiz_controller.handle_book_selection, pattern=r"^quiz_book_"))
	application.add_handler(CallbackQueryHandler(teaching_controller.handle_book_selection, pattern=r"^teach_book_"))
	application.add_handler(CallbackQueryHandler(progress_controller.mark_book_completed, pattern=r"^complete_book_"))

	# Add message handlers
	logging.info("Adding message handlers...")
	application.add_handler(MessageHandler(
		filters.TEXT & ~filters.COMMAND,
		book_selection_controller.handle_text_input
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