# app/controllers/summary_view.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import SessionLocal, Book, Summary
from app.services.book_processor import BookProcessor

async def view_book_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Provides a summary of the currently selected book or allows selection of chapters.
	This is a dedicated command for viewing existing summaries.
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
				f"📝 This is a basic summary. For detailed chapter summaries, please upload the book file by:\n"
				f"1. Clicking the attachment (📎) icon\n"
				f"2. Selecting 'File'\n"
				f"3. Uploading your book in PDF, EPUB, or FB2 format",
				parse_mode='Markdown'
			)
			return

		# If there's only one summary, show it directly
		if len(summaries) == 1:
			summary = summaries[0]
			await update.message.reply_text(
				f"📚 *{book.title}* - *{summary.title}*\n\n"
				f"{summary.summary}\n\n"
				f"Use /quiz to test your knowledge or /teach to practice explaining these concepts.",
				parse_mode='Markdown'
			)
			return

		# If there are multiple summaries (chapters), show a list
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
			reply_markup=reply_markup,
			parse_mode='Markdown'
		)

	except Exception as e:
		logging.error(f"Error in view_book_summary_command: {str(e)}")
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
				"Use /viewsummary to view specific chapter summaries.",
				parse_mode='Markdown'
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

			await query.edit_message_text(message_text, parse_mode='Markdown')

		except Exception as e:
			logging.error(f"Error in handle_summary_selection: {str(e)}")
			await query.edit_message_text("Sorry, there was an error retrieving the summary.")
		finally:
			db.close()