# app/controllers/summary_text.py - UPDATED
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.database.db_handler import SessionLocal, save_message_to_db, save_summary_to_db
from app.services.summarization_service import summarize_with_gemini
from constants.constants import ERROR_MESSAGES


async def summarize_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logging.info("Received text summarization request")
	user_input = update.message.text
	user_id = update.effective_user.id

	db = SessionLocal()
	try:
		# Save the message to the database
		save_message_to_db(db, user_id, user_input)

		if len(user_input.split()) < 10:
			await update.message.reply_text(ERROR_MESSAGES["INVALID_INPUT"])
			return

		# Generate summary
		summary = summarize_with_gemini(user_input)
		save_summary_to_db(db, user_id, title="Short Text", original_text=user_input, summary=summary)

		# Send the summary
		logging.info("Sending summary to user")
		await update.message.reply_text(f"Summary: {summary}")
	except Exception as e:
		logging.error(f"Error in summarize_text_command: {str(e)}")
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])
	finally:
		db.close()