# constants/constants.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

BOT_COMMANDS = {
	"START": "/start",
	"SUMMARIZE_TEXT": "/summarize_text",
	"SUMMARIZE_BOOK": "/summarize_book",
}

ERROR_MESSAGES = {
	"FILE_TOO_LARGE": "Files larger than 2GB are not supported.",
	"INVALID_FILE_TYPE": "Unsupported file type. Please upload PDF, EPUB, or FB2 files.",
	"API_ERROR": "An error occurred while processing your request. Please try again later.",
	"INVALID_INPUT": "Input too short to summarize.",
}

LOGGING_CONFIG = {
	"LOG_FILE": "bot.log",
	"LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")