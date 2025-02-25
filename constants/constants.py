import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env
load_dotenv()

# Configure logging before anything else
logging.basicConfig(
	level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
	format="%(asctime)s - %(levelname)s - %(message)s",
)

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

# Bot and API tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")  # Changed to match .env file

# LLM Configuration
GEMINI_MODEL_NAME = "gemini-pro"  # Default model
GEMINI_MAX_TOKENS = 8192  # Maximum token count for Gemini Pro
GEMINI_TEMPERATURE = 0.2  # Lower temperature for more deterministic outputs

# NLP Processing
CHUNKING_SIZE = 4000  # Default size for text chunks
CHAPTER_MIN_LENGTH = 1000  # Minimum length to consider as a chapter
CHAPTER_MAX_LENGTH = 30000  # Maximum length for a chapter before splitting

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Spaced Repetition Intervals (in days)
SPACED_REPETITION_INTERVALS = {
	"SUMMARY": [1, 3, 7, 30],  # Days to send summary reminders
	"QUIZ": [2, 5, 14],         # Days to send quiz questions
	"TEACHING": [4, 10, 21]     # Days to send teaching prompts
}

# Log configuration
logging.info(f"Database URL: {DATABASE_URL}")
logging.info(f"Logging level: {os.getenv('LOG_LEVEL', 'INFO')}")
logging.info(f"Google API key set: {'Yes' if GENAI_API_KEY else 'No'}")
logging.info(f"Telegram token set: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
logging.info(f"Using Gemini model: {GEMINI_MODEL_NAME}")