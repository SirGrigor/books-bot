# app/controllers/book_management.py - Complete class with all required methods
import logging
from typing import List, Optional, Dict
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import (
	SessionLocal,
	Book,
	UserBook,
	add_custom_book_to_db,
	save_book_selection_to_db,
	get_books_by_category,
	search_books as db_search_books,
	get_book_categories,
	batch_import_books
)
from app.services.reminders_service import schedule_spaced_repetition

class BookManagementController:
	"""
	Controller for enhanced book management functionality including:
	- Book browsing with categories
	- Advanced book search and filtering
	- Batch book imports
	- Book recommendations
	"""

	async def browse_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handle /browsebooks command - shows books by category with pagination
		"""
		db = SessionLocal()
		try:
			# Get all categories
			all_books = db.query(Book).all()
			categories = set()
			for book in all_books:
				if book.category:
					categories.add(book.category)

			# Add default categories if none found
			if not categories:
				categories = {"Fiction", "Non-Fiction", "Self-Help", "Business", "Science"}

			# Create keyboard with categories
			keyboard = []
			for category in sorted(categories):
				keyboard.append([InlineKeyboardButton(
					f"📚 {category}",
					callback_data=f"category_{category}"
				)])

			# Add options for all books and adding custom book
			keyboard.append([InlineKeyboardButton("🔍 Search Books", callback_data="search_books")])
			keyboard.append([InlineKeyboardButton("➕ Add New Book", callback_data="add_new_book")])
			keyboard.append([InlineKeyboardButton("📋 Import Book List", callback_data="import_books")])

			reply_markup = InlineKeyboardMarkup(keyboard)

			# Handle the message properly based on update type
			if update.callback_query:
				await update.callback_query.edit_message_text(
					"Browse books by category or add new books to your collection:",
					reply_markup=reply_markup
				)
			else:
				await update.message.reply_text(
					"Browse books by category or add new books to your collection:",
					reply_markup=reply_markup
				)

		except Exception as e:
			logging.error(f"Error in browse_books: {str(e)}")
			if update.callback_query:
				await update.callback_query.edit_message_text("Sorry, there was an error browsing books.")
			else:
				await update.message.reply_text("Sorry, there was an error browsing books.")
		finally:
			db.close()

	async def handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles selection of a book category
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("category_"):
			category = query.data[9:]  # Remove "category_" prefix

			db = SessionLocal()
			try:
				# Get books for this category, with pagination
				page = context.user_data.get("page", 1) if context.user_data else 1
				books_per_page = 5
				offset = (page - 1) * books_per_page

				# Query books with category filter
				books = db.query(Book).filter(Book.category == category).offset(offset).limit(books_per_page).all()
				total_books = db.query(Book).filter(Book.category == category).count()

				if not books:
					await query.edit_message_text(
						f"No books found in category '{category}'. Would you like to add one?",
						reply_markup=InlineKeyboardMarkup([[
							InlineKeyboardButton("➕ Add New Book", callback_data="add_new_book")
						], [
							InlineKeyboardButton("« Back to Categories", callback_data="back_to_categories")
						]])
					)
					return

				# Create keyboard with book options
				keyboard = []
				for book in books:
					book_info = f"{book.title}"
					if book.author:
						book_info += f" by {book.author}"
					keyboard.append([InlineKeyboardButton(book_info, callback_data=f"book_{book.id}")])

				# Add pagination controls if needed
				pagination = []
				if page > 1:
					pagination.append(InlineKeyboardButton("« Previous", callback_data=f"page_{page-1}_{category}"))

				total_pages = (total_books + books_per_page - 1) // books_per_page
				pagination.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="noop"))

				if page < total_pages:
					pagination.append(InlineKeyboardButton("Next »", callback_data=f"page_{page+1}_{category}"))

				if pagination:
					keyboard.append(pagination)

				# Add navigation buttons
				keyboard.append([InlineKeyboardButton("« Back to Categories", callback_data="back_to_categories")])
				keyboard.append([InlineKeyboardButton("➕ Add New Book to This Category", callback_data=f"add_book_to_{category}")])

				reply_markup = InlineKeyboardMarkup(keyboard)

				await query.edit_message_text(
					f"📚 Books in category: {category}\nSelect a book to add to your reading list:",
					reply_markup=reply_markup
				)

			except Exception as e:
				logging.error(f"Error in handle_category_selection: {str(e)}")
				await query.edit_message_text("Sorry, there was an error retrieving books.")
			finally:
				db.close()

	async def handle_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles pagination for book browsing
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("page_"):
			# Parse page number and category
			parts = query.data.split('_')
			page = int(parts[1])
			category = parts[2] if len(parts) > 2 else None

			# Store current page in user_data
			if not context.user_data:
				context.user_data = {}
			context.user_data["page"] = page

			# Reuse category selection handler with updated page
			if category:
				# Re-trigger category selection with new page
				query.data = f"category_{category}"
				await self.handle_category_selection(update, context)
			else:
				# If no category specified, go back to main browse
				await self.browse_books(update, context)

	async def search_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles book search functionality
		"""
		query = update.callback_query
		if query:
			await query.answer()
			await query.edit_message_text(
				"Please enter a search term for book title or author.\n"
				"Type your search query:"
			)
		else:
			await update.message.reply_text(
				"Please enter a search term for book title or author.\n"
				"Type your search query:"
			)

		# Set context to await search query
		if not context.user_data:
			context.user_data = {}
		context.user_data["awaiting_search_query"] = True

	async def handle_search_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Processes book search query
		"""
		search_query = update.message.text.strip()

		db = SessionLocal()
		try:
			# Search for books matching the query in title or author
			books = db.query(Book).filter(
				(Book.title.ilike(f"%{search_query}%")) |
				(Book.author.ilike(f"%{search_query}%"))
			).limit(10).all()

			if not books:
				# No books found - offer to add new book
				keyboard = [
					[InlineKeyboardButton(f"➕ Add '{search_query}' as new book", callback_data=f"add_book_title_{search_query}")],
					[InlineKeyboardButton("🔍 Try another search", callback_data="search_books")],
					[InlineKeyboardButton("« Back to Browse", callback_data="back_to_categories")]
				]

				await update.message.reply_text(
					f"No books found matching '{search_query}'.",
					reply_markup=InlineKeyboardMarkup(keyboard)
				)
				return

			# Display search results
			keyboard = []
			for book in books:
				book_info = f"{book.title}"
				if book.author:
					book_info += f" by {book.author}"
				keyboard.append([InlineKeyboardButton(book_info, callback_data=f"book_{book.id}")])

			# Add navigation options
			keyboard.append([InlineKeyboardButton("🔍 New Search", callback_data="search_books")])
			keyboard.append([InlineKeyboardButton("« Back to Browse", callback_data="back_to_categories")])

			await update.message.reply_text(
				f"📚 Search results for '{search_query}':\nSelect a book to add to your reading list:",
				reply_markup=InlineKeyboardMarkup(keyboard)
			)

		except Exception as e:
			logging.error(f"Error in handle_search_query: {str(e)}")
			await update.message.reply_text("Sorry, there was an error searching for books.")
		finally:
			db.close()

		# Clear awaiting state
		if context.user_data:
			context.user_data.pop("awaiting_search_query", None)

	async def add_new_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles adding a new book with structured information
		"""
		query = update.callback_query
		if query:
			await query.answer()
			await query.edit_message_text(
				"📝 Add a New Book\n\n"
				"Please provide the book information in the following format:\n\n"
				"Title: [Book Title]\n"
				"Author: [Author Name] (optional)\n"
				"Category: [Category] (optional)\n"
				"Description: [Short description] (optional)\n\n"
				"For example:\n"
				"Title: The Great Gatsby\n"
				"Author: F. Scott Fitzgerald\n"
				"Category: Fiction\n"
				"Description: A story of wealth, love and the American Dream."
			)
		else:
			await update.message.reply_text(
				"📝 Add a New Book\n\n"
				"Please provide the book information in the following format:\n\n"
				"Title: [Book Title]\n"
				"Author: [Author Name] (optional)\n"
				"Category: [Category] (optional)\n"
				"Description: [Short description] (optional)\n\n"
				"For example:\n"
				"Title: The Great Gatsby\n"
				"Author: F. Scott Fitzgerald\n"
				"Category: Fiction\n"
				"Description: A story of wealth, love and the American Dream."
			)

		# Set context to await book details
		if not context.user_data:
			context.user_data = {}
		context.user_data["awaiting_book_details"] = True

	async def handle_book_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Processes new book details submitted by user
		"""
		book_details_text = update.message.text.strip()

		# Parse the book details
		book_info = self._parse_book_details(book_details_text)

		if not book_info.get('title'):
			await update.message.reply_text(
				"⚠️ Book title is required. Please try again and include 'Title: [Book Title]' in your message."
			)
			return

		user_id = update.effective_user.id

		db = SessionLocal()
		try:
			# Add the book to the database
			book = add_custom_book_to_db(
				db,
				book_info.get('title'),
				user_id,
				author=book_info.get('author'),
				description=book_info.get('description'),
				category=book_info.get('category'),
				tags=book_info.get('tags')
			)

			# Store book_id in context for reminders
			if not context.chat_data:
				context.chat_data = {}
			context.chat_data["current_book_id"] = book.id

			# Schedule the spaced repetition reminders
			await schedule_spaced_repetition(context, user_id, book.title)

			# Create confirmation message
			confirmation = f"✅ Added to your reading list:\n\n"
			confirmation += f"📚 *{book.title}*\n"
			if book.author:
				confirmation += f"👤 Author: {book.author}\n"
			if book.category:
				confirmation += f"🏷️ Category: {book.category}\n"

			confirmation += "\nI've set up spaced repetition reminders to help you remember the key concepts."

			# Create button to browse more books
			keyboard = [
				[InlineKeyboardButton("📝 View Summary", callback_data=f"summary_{book.id}")],
				[InlineKeyboardButton("📚 Browse More Books", callback_data="back_to_categories")]
			]

			await update.message.reply_text(
				confirmation,
				parse_mode='Markdown',
				reply_markup=InlineKeyboardMarkup(keyboard)
			)

		except Exception as e:
			logging.error(f"Error adding book: {str(e)}")
			await update.message.reply_text("Sorry, there was an error adding the book to your collection.")
		finally:
			db.close()

		# Clear awaiting state
		if context.user_data:
			context.user_data.pop("awaiting_book_details", None)

	async def handle_import_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles bulk import of books
		"""
		query = update.callback_query
		if query:
			await query.answer()
			await query.edit_message_text(
				"📚 Import Multiple Books\n\n"
				"Please provide a list of books, one per line, in the following format:\n\n"
				"Title | Author | Category (optional)\n\n"
				"For example:\n"
				"The Great Gatsby | F. Scott Fitzgerald | Fiction\n"
				"Thinking, Fast and Slow | Daniel Kahneman | Psychology\n"
				"Atomic Habits | James Clear | Self-Help\n\n"
				"The separator '|' is important, but author and category are optional."
			)
		else:
			await update.message.reply_text(
				"📚 Import Multiple Books\n\n"
				"Please provide a list of books, one per line, in the following format:\n\n"
				"Title | Author | Category (optional)\n\n"
				"For example:\n"
				"The Great Gatsby | F. Scott Fitzgerald | Fiction\n"
				"Thinking, Fast and Slow | Daniel Kahneman | Psychology\n"
				"Atomic Habits | James Clear | Self-Help\n\n"
				"The separator '|' is important, but author and category are optional."
			)

		# Set context to await book list
		if not context.user_data:
			context.user_data = {}
		context.user_data["awaiting_book_import"] = True

	async def handle_book_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Processes book import list
		"""
		import_text = update.message.text.strip()
		lines = import_text.split('\n')

		user_id = update.effective_user.id
		added_books = []
		skipped_books = []

		# Process status message
		status_message = await update.message.reply_text("Processing your book list...")

		db = SessionLocal()
		try:
			for line in lines:
				line = line.strip()
				if not line:
					continue

				# Parse the line
				parts = [part.strip() for part in line.split('|')]
				title = parts[0]

				if not title:
					skipped_books.append("(Empty title)")
					continue

				author = parts[1] if len(parts) > 1 and parts[1].strip() else None
				category = parts[2] if len(parts) > 2 and parts[2].strip() else None

				try:
					# Check if this book already exists
					existing_book = db.query(Book).filter(Book.title == title).first()

					if existing_book:
						# Just link existing book to user
						save_book_selection_to_db(db, user_id, existing_book.id)
						added_books.append(f"{title}" + (f" by {author}" if author else ""))
					else:
						# Add new book
						book = add_custom_book_to_db(
							db, title, user_id, author=author, category=category
						)
						added_books.append(f"{title}" + (f" by {author}" if author else ""))
				except Exception as e:
					logging.error(f"Error adding book '{title}': {str(e)}")
					skipped_books.append(f"{title}" + (f" by {author}" if author else ""))

			# Create summary message
			result = f"📚 Import Results:\n\n"
			result += f"✅ Added {len(added_books)} books to your collection\n"
			if skipped_books:
				result += f"⚠️ Skipped {len(skipped_books)} books\n"

			# If books were added, schedule reminders for the first one
			if added_books and not context.chat_data.get("current_book_id"):
				first_book = db.query(Book).filter(Book.title == added_books[0].split(" by ")[0]).first()
				if first_book:
					context.chat_data = context.chat_data or {}
					context.chat_data["current_book_id"] = first_book.id
					await schedule_spaced_repetition(context, user_id, first_book.title)

			# Create button to browse books
			keyboard = [
				[InlineKeyboardButton("📚 Browse Your Books", callback_data="back_to_categories")]
			]

			await status_message.edit_text(
				result,
				reply_markup=InlineKeyboardMarkup(keyboard)
			)

		except Exception as e:
			logging.error(f"Error in book import: {str(e)}")
			await status_message.edit_text("Sorry, there was an error importing your books.")
		finally:
			db.close()

		# Clear awaiting state
		if context.user_data:
			context.user_data.pop("awaiting_book_import", None)

	async def handle_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles navigation callbacks like back buttons
		"""
		query = update.callback_query
		await query.answer()

		if query.data == "back_to_categories":
			# Go back to browse books view
			await self.browse_books(update, context)
		elif query.data.startswith("add_book_to_"):
			# Add book to specific category
			category = query.data[12:]  # Remove "add_book_to_" prefix

			if not context.user_data:
				context.user_data = {}

			context.user_data["book_category"] = category
			await self.add_new_book(update, context)
		elif query.data.startswith("add_book_title_"):
			# Add book with pre-filled title
			title = query.data[14:]  # Remove "add_book_title_" prefix

			await query.edit_message_text(
				f"📝 Add Book: {title}\n\n"
				f"Please provide additional information:\n\n"
				f"Title: {title}\n"
				f"Author: [Author Name]\n"
				f"Category: [Category]\n"
				f"Description: [Short description]\n\n"
				f"You can edit the title if needed."
			)

			# Set context to await book details
			if not context.user_data:
				context.user_data = {}
			context.user_data["awaiting_book_details"] = True

	def _parse_book_details(self, text: str) -> Dict[str, str]:
		"""
		Parses structured book details from user input text
		"""
		book_info = {}

		# Extract fields using regex
		title_match = re.search(r"Title:\s*(.+?)(?=\n\w+:|$)", text, re.IGNORECASE | re.DOTALL)
		if title_match:
			book_info["title"] = title_match.group(1).strip()

		author_match = re.search(r"Author:\s*(.+?)(?=\n\w+:|$)", text, re.IGNORECASE | re.DOTALL)
		if author_match:
			book_info["author"] = author_match.group(1).strip()

		category_match = re.search(r"Category:\s*(.+?)(?=\n\w+:|$)", text, re.IGNORECASE | re.DOTALL)
		if category_match:
			book_info["category"] = category_match.group(1).strip()

		description_match = re.search(r"Description:\s*(.+?)(?=\n\w+:|$)", text, re.IGNORECASE | re.DOTALL)
		if description_match:
			book_info["description"] = description_match.group(1).strip()

		# If no title found via regex, use the first line as a fallback
		if not book_info.get("title"):
			first_line = text.split('\n')[0].strip()
			if first_line:
				book_info["title"] = first_line

		return book_info