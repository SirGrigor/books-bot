# app/controllers/summary_book.py - ENHANCED

from telegram import Update
from telegram.ext import ContextTypes
from app.utils.file_processing import extract_text_from_pdf, extract_text_from_epub, extract_text_from_fb2
from app.services.book_processor import BookProcessor
from app.database.db_handler import save_message_to_db, SessionLocal
from constants.constants import ERROR_MESSAGES
import logging
import os

async def summarize_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles document uploads (books) and initiates the book processing workflow.
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

	db = SessionLocal()
	try:
		# Save the file upload message to the database
		save_message_to_db(db, user_id, f"Uploaded file: {file.file_name}")

		# Check file extension
		if not (file_path.endswith(".pdf") or file_path.endswith(".epub") or file_path.endswith(".fb2")):
			await update.message.reply_text(ERROR_MESSAGES["INVALID_FILE_TYPE"])
			return

		# Download the file
		logging.info(f"Downloading file: {file.file_name}")
		new_file = await context.bot.get_file(file.file_id)
		await new_file.download_to_drive(file_path)

		# Send an initial response to the user
		await update.message.reply_text(
			"📚 I've received your book file and I'm processing it now. "
			"This might take a few minutes depending on the size of the book.\n\n"
			"I'll analyze the content, extract chapters, and create summaries optimized for retention."
		)

		# Initialize BookProcessor
		processor = BookProcessor()

		# Process the book asynchronously
		processing_result = await processor.process_uploaded_book(file_path, str(user_id), book_id)

		if not processing_result.get("success", False):
			error_message = processing_result.get("error", "Unknown error")
			logging.error(f"Book processing failed: {error_message}")
			await update.message.reply_text(
				f"❌ Sorry, I couldn't process this book properly: {error_message}\n\n"
				"Please try another file or format."
			)
			return

		# Get processing details
		chapters = processing_result.get("chapters", [])
		total_chapters = processing_result.get("total_chapters", 0)

		# Send success message with book overview
		if total_chapters > 0:
			# Send a summary of the processed book
			overview_message = (
				f"✅ Book successfully processed! I found {total_chapters} chapters.\n\n"
				f"Here's a summary of the first chapter:\n\n"
			)

			# Add the first chapter summary if available
			if chapters and len(chapters) > 0:
				first_chapter = chapters[0]
				overview_message += f"*{first_chapter.get('title', 'Chapter 1')}*\n\n"
				overview_message += first_chapter.get('summary', '')[:800] + "...\n\n"

			overview_message += (
				"I've set up spaced repetition reminders to help you remember the key concepts.\n"
				"You'll receive reminders at optimal intervals to maximize retention.\n\n"
				"Use /summary to view chapter summaries, /quiz to test your knowledge, and /teach to practice explaining concepts."
			)

			await update.message.reply_text(overview_message)
		else:
			await update.message.reply_text(
				"✅ Book processed, but I couldn't detect clear chapter divisions.\n\n"
				"I've created a single summary for the entire content. Use /summary to view it."
			)

	except Exception as e:
		logging.error(f"Error in summarize_book_command: {str(e)}")
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])
	finally:
		db.close()

async def get_book_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Provides a summary of the currently selected book or allows selection of chapters.
	"""
	user_id = update.effective_user.id

	# Check if a book is currently selected
	book_id = None
	if hasattr(context, 'chat_data') and context.chat_data:
		book_id = context.chat_data.get("current_book_id")

	if not book_id:
		await update.message.reply_text(
			"You don't have a book selected. Use /selectbook to choose a book first."
		)
		return

	db = SessionLocal()
	try:
		# Get summaries for this book
		from app.database.db_handler import Summary, Book

		# Get the book title
		book = db.query(Book).filter(Book.id == book_id).first()
		if not book:
			await update.message.reply_text("Book not found. Please select a book first.")
			return

		# Get summaries for this book
		summaries = db.query(Summary).filter(
			Summary.user_id == str(user_id),
			Summary.book_id == book_id
		).order_by(Summary.id.desc()).all()

		if not summaries or len(summaries) == 0:
			# No summaries found, generate an initial one
			processor = BookProcessor()
			initial_summary = await processor.generate_initial_summary(book_id, str(user_id))

			await update.message.reply_text(
				f"📚 *{book.title}*\n\n"
				f"{initial_summary}\n\n"
				"To get more detailed summaries, please upload the book file using the document attachment feature."
			)
			return

		# If there's only one summary, show it directly
		if len(summaries) == 1:
			summary = summaries[0]
			await update.message.reply_text(
				f"📚 *{book.title}* - *{summary.title}*\n\n"
				f"{summary.summary}\n\n"
				"Use /quiz to test your knowledge or /teach to practice explaining these concepts."
			)
			return

		# If there are multiple summaries (chapters), show a list
		from telegram import InlineKeyboardButton, InlineKeyboardMarkup

		# Create chapter buttons - limit to 10 to avoid exceeding Telegram's limits
		keyboard = []
		chapter_count = min(len(summaries), 10)

		for i in range(chapter_count):
			summary = summaries[i]
			keyboard.append([InlineKeyboardButton(
				summary.title or f"Chapter {i+1}",
				callback_data=f"summary_{summary.id}"
			)])

		# Add a button for the full book overview
		keyboard.append([InlineKeyboardButton("Full Book Overview", callback_data=f"summary_overview_{book_id}")])

		reply_markup = InlineKeyboardMarkup(keyboard)

		await update.message.reply_text(
			f"📚 *{book.title}*\n\n"
			"I've divided this book into chapters. Select one to view its summary:",
			reply_markup=reply_markup
		)

	except Exception as e:
		logging.error(f"Error in get_book_summary_command: {str(e)}")
		await update.message.reply_text("Sorry, there was an error retrieving the book summary.")
	finally:
		db.close()

async def handle_summary_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles the selection of a specific chapter summary.
	"""
	query = update.callback_query
	await query.answer()

	if query.data.startswith("summary_overview_"):
		# Show book overview
		book_id = int(query.data.split("_")[2])

		db = SessionLocal()
		try:
			# Get the book
			from app.database.db_handler import Book, Summary
			book = db.query(Book).filter(Book.id == book_id).first()

			if not book:
				await query.edit_message_text("Book not found.")
				return

			# Get the first/most recent summary to use as an overview
			summary = db.query(Summary).filter(
				Summary.user_id == str(update.effective_user.id),
				Summary.book_id == book_id
			).order_by(Summary.id.desc()).first()

			if not summary:
				await query.edit_message_text(
					f"No summary available for '{book.title}'. "
					f"Try uploading the book file first."
				)
				return

			# Generate a book overview
			processor = BookProcessor()
			overview = await processor.generate_initial_summary(book_id, str(update.effective_user.id))

			await query.edit_message_text(
				f"📚 *{book.title}* - Overview\n\n"
				f"{overview}\n\n"
				"Use /summary to view specific chapter summaries."
			)

		except Exception as e:
			logging.error(f"Error in handle_summary_selection for overview: {str(e)}")
			await query.edit_message_text("Sorry, there was an error retrieving the book overview.")
		finally:
			db.close()

	elif query.data.startswith("summary_"):
		# Show specific summary
		summary_id = int(query.data.split("_")[1])

		db = SessionLocal()
		try:
			# Get the summary
			from app.database.db_handler import Summary, Book
			summary = db.query(Summary).filter(Summary.id == summary_id).first()

			if not summary:
				await query.edit_message_text("Summary not found.")
				return

			# Get the book title
			book = db.query(Book).filter(Book.id == summary.book_id).first()
			book_title = book.title if book else "Book"

			# Format and send the summary
			message_text = (
				f"📚 *{book_title}* - *{summary.title}*\n\n"
				f"{summary.summary}\n\n"
				"Use /quiz to test your knowledge or /teach to practice explaining these concepts."
			)

			# Handle message length limits
			if len(message_text) > 4096:
				message_text = message_text[:4093] + "..."

			await query.edit_message_text(message_text)

		except Exception as e:
			logging.error(f"Error in handle_summary_selection: {str(e)}")
			await query.edit_message_text("Sorry, there was an error retrieving the summary.")
		finally:
			db.close()