import logging
import os
from datetime import time

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

# Configure logging
configure_logging()

logging.info("Starting bot...")

def main():
	# Initialize the database
	try:
		init_database()
	except Exception as e:
		logging.error(f"Error initializing database: {str(e)}")
		# Continue anyway, as the basic functionality should still work

	# Initialize the bot
	application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

	# Initialize controllers
	start_controller = StartController()
	book_selection_controller = BookSelectionController()
	quiz_controller = QuizController()
	teaching_service = generate_discussion_prompt  # Pass the function
	teaching_controller = TeachingController(teaching_service)
	progress_controller = ProgressController()

	# Add command handlers
	application.add_handler(CommandHandler("start", start_controller.start))
	application.add_handler(CommandHandler("help", start_controller.help))
	application.add_handler(CommandHandler("selectbook", book_selection_controller.select_book))
	application.add_handler(CommandHandler("addbook", book_selection_controller.add_custom_book_command))
	application.add_handler(CommandHandler("summary", summarize_text_command))
	application.add_handler(CommandHandler("quiz", quiz_controller.send_quiz))
	application.add_handler(CommandHandler("teach", teaching_controller.send_teaching_prompt))
	application.add_handler(CommandHandler("progress", progress_controller.show_progress))

	# Add callback query handler for inline keyboards
	application.add_handler(CallbackQueryHandler(start_controller.handle_menu_callback, pattern=r"^menu_"))
	application.add_handler(CallbackQueryHandler(book_selection_controller.handle_book_selection, pattern=r"^book_"))
	application.add_handler(CallbackQueryHandler(quiz_controller.handle_book_selection, pattern=r"^quiz_book_"))
	application.add_handler(CallbackQueryHandler(teaching_controller.handle_book_selection, pattern=r"^teach_book_"))
	application.add_handler(CallbackQueryHandler(progress_controller.mark_book_completed, pattern=r"^complete_book_"))

	# Add message handlers
	# Only parse non-command text messages for summarizing when not in a specific context
	application.add_handler(MessageHandler(
		filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.CALLBACK_QUERY,
		book_selection_controller.handle_text_input
	))
	application.add_handler(MessageHandler(filters.Document.ALL, summarize_book_command))

	# Schedule the reminder job - run every hour
	application.job_queue.run_repeating(process_due_reminders, interval=3600, first=60)

	# Start polling
	application.run_polling()

if __name__ == "__main__":
	main()