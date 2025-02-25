import logging
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.controllers.summary_text import summarize_text_command
from app.controllers.summary_book import summarize_book_command
from app.utils.logging_config import configure_logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)
configure_logging()

logging.info("Starting bot...")

def main():
	application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

	application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Welcome! Use /summarize_text or /summarize_book.")))
	application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_text_command))
	application.add_handler(MessageHandler(filters.Document.ALL, summarize_book_command))

	application.run_polling()

if __name__ == "__main__":
	main()