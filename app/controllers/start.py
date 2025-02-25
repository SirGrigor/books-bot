from telegram import Update
from telegram.ext import ContextTypes

from app.database.db_handler import save_user_to_db, SessionLocal


class StartController:
	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user = update.effective_user
		username = user.username or user.first_name
		db = SessionLocal()  # Use SessionLocal instead of Session
		save_user_to_db(db, user.id, user.username, user.first_name)
		await update.message.reply_text(f"Welcome, {username}!")
		db.close()

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
