from telegram import Update
from telegram.ext import ContextTypes

class StartController:
	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Displays a welcome message and lists all available commands.
		"""
		if update.message is None:
			return  # Exit if there's no message to reply to

		await update.message.reply_text(
			"Welcome to the Book Retention Bot! Here are the available commands:\n"
			"/help - Get help and see all commands.\n"
			"/summary <text> - Get a summary of a short text.\n"
			"/summary_book - Upload a book file (TXT, EPUB, PDF, FB2) to get chapter-wise summaries."
		)

	async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Displays a help message with all available commands.
		"""
		if update.message is None:
			return  # Exit if there's no message to reply to

		await update.message.reply_text(
			"Available commands:\n"
			"/summary <text> - Get a summary of a short text.\n"
			"/summary_book - Upload a book file (TXT, EPUB, PDF, FB2) to get chapter-wise summaries."
		)