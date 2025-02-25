# app/controllers/summary_book.py
from telegram import Update
from telegram.ext import ContextTypes
from app.utils.file_processing import extract_text_from_pdf, extract_text_from_epub, extract_text_from_fb2
from app.utils.chunking import split_into_chunks
from app.services.summarization_service import summarize_with_gemini
from app.database.db_handler import save_message_to_db, save_summary_to_db
from constants.constants import ERROR_MESSAGES
from sqlalchemy.orm import Session
import logging
import os

async def summarize_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logging.info("Received book upload request")  # Add this line
	file = update.message.document
	file_path = f"./downloads/{file.file_name}"
	user_id = update.effective_user.id

	# Ensure the downloads directory exists
	os.makedirs("./downloads", exist_ok=True)  # Add this line

	db = Session()
	try:
		# Save the file upload message to the database
		save_message_to_db(db, user_id, f"Uploaded file: {file.file_name}")

		# Download the file
		logging.info(f"Downloading file: {file.file_name}")  # Add this line
		new_file = await context.bot.get_file(file.file_id)
		await new_file.download_to_drive(file_path)

		# Extract text based on file type
		if file_path.endswith(".pdf"):
			full_text = extract_text_from_pdf(file_path)
		elif file_path.endswith(".epub"):
			full_text = extract_text_from_epub(file_path)
		elif file_path.endswith(".fb2"):
			full_text = extract_text_from_fb2(file_path)
		else:
			await update.message.reply_text(ERROR_MESSAGES["INVALID_FILE_TYPE"])
			return

		# Summarize text in chunks
		chunks = split_into_chunks(full_text)
		summaries = [summarize_with_gemini(chunk) for chunk in chunks]
		final_summary = "\n".join(summaries)

		# Save the summary to the database
		save_summary_to_db(db, user_id, title="Book Summary", original_text=full_text, summary=final_summary)

		# Send the summary
		logging.info("Sending summary to user")  # Add this line
		await update.message.reply_text(f"Summary: {final_summary[:4096]}")
	except Exception as e:
		logging.error(f"Error in summarize_book_command: {str(e)}")  # Add this line
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])
	finally:
		db.close()