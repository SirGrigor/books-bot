# main.py
import logging
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.controllers.start import StartController
from app.controllers.summary_text import summarize_text_command
from app.controllers.summary_book import summarize_book_command
from app.utils.logging_config import configure_logging

# Configure logging
configure_logging()

logging.info("Starting bot...")

def main():
	# Initialize the bot
	application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

	# Add command handlers
	start_controller = StartController()
	application.add_handler(CommandHandler("start", start_controller.start))
	application.add_handler(CommandHandler("help", start_controller.help))

	# Add message handlers
	application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_text_command))
	application.add_handler(MessageHandler(filters.Document.ALL, summarize_book_command))

	# Start polling
	application.run_polling()

if __name__ == "__main__":
	main()