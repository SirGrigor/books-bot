# app/controllers/summary_text.py
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.database.db_handler import SessionLocal, save_message_to_db, save_summary_to_db
from app.services.summarization_service import summarize_with_gemini
from constants.constants import ERROR_MESSAGES


async def summarize_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles text summarization for general text input (not related to books).
	This command summarizes any text that the user sends.
	"""
	logging.info("Received text summarization request")
	user_input = update.message.text
	user_id = update.effective_user.id

	db = SessionLocal()
	try:
		# Save the message to the database
		save_message_to_db(db, user_id, user_input)

		if len(user_input.split()) < 10:
			await update.message.reply_text(
				"⚠️ Your text is too short to summarize. Please provide a longer passage (at least 10 words)."
			)
			return

		# Send a processing message
		processing_message = await update.message.reply_text(
			"🔄 Processing your text... This will take just a moment."
		)

		# Generate summary
		try:
			summary = summarize_with_gemini(user_input)

			# Save the summary to database without book_id (it's not book-related)
			save_summary_to_db(db, user_id, title="Text Summary", original_text=user_input, summary=summary)

			# Send the summary
			await context.bot.edit_message_text(
				f"📝 Here's your summary:\n\n{summary}",
				chat_id=update.effective_chat.id,
				message_id=processing_message.message_id
			)

		except Exception as e:
			logging.error(f"Error in text summarization: {str(e)}")
			await context.bot.edit_message_text(
				"❌ Sorry, I encountered an error while summarizing your text. Please try again with different content.",
				chat_id=update.effective_chat.id,
				message_id=processing_message.message_id
			)

	except Exception as e:
		logging.error(f"Error in summarize_text_command: {str(e)}")
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])
	finally:
		db.close()