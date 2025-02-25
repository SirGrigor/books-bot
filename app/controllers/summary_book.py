# app/controllers/summary_book.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.utils.file_processing import extract_text_from_pdf, extract_text_from_epub, extract_text_from_fb2
from app.services.book_processor import BookProcessor
from app.database.db_handler import save_message_to_db, SessionLocal
from constants.constants import ERROR_MESSAGES
import os

async def summarize_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles document uploads (books) and initiates the book processing workflow.
	Enhanced with better progress updates and error handling.
	"""
	logging.info("Received book upload request")
	file = update.message.document
	file_path = f"./downloads/{file.file_name}"
	user_id = update.effective_user.id

	# Ensure the downloads directory exists
	os.makedirs("./downloads", exist_ok=True)

	# Get the current book_id from context if it exists
	book_id = None
	if hasattr(context, 'chat_data') and context.chat_data:
		book_id = context.chat_data.get("current_book_id")

	# Check if a book is selected
	if not book_id:
		await update.message.reply_text(
			"⚠️ You haven't selected a book yet! Please use /selectbook first, then upload the file."
		)
		return

	db = SessionLocal()
	try:
		# Save the file upload message to the database
		save_message_to_db(db, user_id, f"Uploaded file: {file.file_name}")

		# Enhanced file type validation with clearer error messages
		if not (file_path.lower().endswith(".pdf") or
				file_path.lower().endswith(".epub") or
				file_path.lower().endswith(".fb2")):
			await update.message.reply_text(
				"⚠️ Unsupported file format. Please upload your book in PDF, EPUB, or FB2 format only."
			)
			return

		# Check file size (limit to 50MB to avoid processing issues)
		if file.file_size > 50 * 1024 * 1024:  # 50MB in bytes
			await update.message.reply_text(
				"⚠️ File is too large (over 50MB). Please upload a smaller file or try a different format."
			)
			return

		# Send a more informative initial response with progress indicator
		initial_message = await update.message.reply_text(
			"📚 I've received your book file and I'm processing it now... (0%)\n\n"
			"This might take a few minutes depending on the book size. I'll keep you updated on the progress."
		)

		# Download the file
		logging.info(f"Downloading file: {file.file_name}")
		new_file = await context.bot.get_file(file.file_id)
		await new_file.download_to_drive(file_path)

		# Update progress
		await context.bot.edit_message_text(
			"📚 Processing your book... (25%)\n"
			"✅ File downloaded successfully\n"
			"⏳ Analyzing text content...",
			chat_id=update.effective_chat.id,
			message_id=initial_message.message_id
		)

		# Initialize BookProcessor
		processor = BookProcessor()

		# Process the book asynchronously
		processing_result = await processor.process_uploaded_book(file_path, str(user_id), book_id)

		if not processing_result.get("success", False):
			error_message = processing_result.get("error", "Unknown error")
			logging.error(f"Book processing failed: {error_message}")
			await context.bot.edit_message_text(
				f"❌ Sorry, I couldn't process this book properly: {error_message}\n\n"
				"Please try another file or format.",
				chat_id=update.effective_chat.id,
				message_id=initial_message.message_id
			)
			return

		# Update progress
		await context.bot.edit_message_text(
			"📚 Processing your book... (75%)\n"
			"✅ File downloaded successfully\n"
			"✅ Text content analyzed\n"
			"⏳ Generating summaries and learning materials...",
			chat_id=update.effective_chat.id,
			message_id=initial_message.message_id
		)

		# Get processing details
		chapters = processing_result.get("chapters", [])
		total_chapters = processing_result.get("total_chapters", 0)

		# Final success message with book overview
		if total_chapters > 0:
			# Send a summary of the processed book
			overview_message = (
				f"✅ Book successfully processed! (100%)\n\n"
				f"📊 Processing Results:\n"
				f"• Found {total_chapters} chapters\n"
				f"• Created chapter summaries\n"
				f"• Generated quiz questions\n"
				f"• Set up spaced repetition reminders\n\n"
				f"Here's a preview of the first chapter:\n\n"
			)

			# Add the first chapter summary if available
			if chapters and len(chapters) > 0:
				first_chapter = chapters[0]
				overview_message += f"*{first_chapter.get('title', 'Chapter 1')}*\n\n"
				overview_message += first_chapter.get('summary', '')[:500] + "...\n\n"

			overview_message += (
				"📝 Use /viewsummary to browse all chapter summaries\n"
				"🧠 Use /quiz to test your knowledge\n"
				"👨‍🏫 Use /teach to practice explaining concepts\n"
				"📈 Use /progress to track your retention"
			)

			await context.bot.edit_message_text(
				overview_message,
				chat_id=update.effective_chat.id,
				message_id=initial_message.message_id,
				parse_mode='Markdown'
			)
		else:
			await context.bot.edit_message_text(
				"✅ Book processed successfully! (100%)\n\n"
				"I couldn't detect clear chapter divisions, so I've created a single summary for the entire content.\n\n"
				"Use /viewsummary to view it.",
				chat_id=update.effective_chat.id,
				message_id=initial_message.message_id
			)

	except Exception as e:
		logging.error(f"Error in summarize_book_command: {str(e)}")
		await update.message.reply_text(
			"❌ Sorry, I encountered an error while processing your book file. Please try again later or with a different file format."
		)
	finally:
		db.close()
		# Clean up the file
		try:
			os.remove(file_path)
			logging.info(f"Removed temporary file: {file_path}")
		except Exception as e:
			logging.warning(f"Failed to remove temporary file: {str(e)}")