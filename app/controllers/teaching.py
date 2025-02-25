# app/controllers/teaching.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database.db_handler import SessionLocal, get_user_books
import google.generativeai as genai
from constants.constants import GENAI_API_KEY

class TeachingController:
	def __init__(self, teaching_service):
		self.teaching_service = teaching_service
		# Initialize the Gemini client
		genai.configure(api_key=GENAI_API_KEY)
		self.model = genai.GenerativeModel('gemini-pro')

	async def send_teaching_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, summary=None):
		"""
		Sends a teaching prompt to help the user solidify their understanding.
		Can be triggered by /teach command or as part of spaced repetition.
		"""
		user_id = update.effective_user.id

		# If summary wasn't provided (e.g., from a spaced repetition reminder)
		if not summary:
			db = SessionLocal()
			try:
				# Get the user's books
				user_books = get_user_books(db, user_id)

				if not user_books or len(user_books) == 0:
					await update.message.reply_text(
						"You don't have any books in your reading list yet. "
						"Use /selectbook to choose a book or /addbook to add a custom one."
					)
					return

				# Create an inline keyboard with book options
				keyboard = []
				for user_book in user_books:
					book = user_book.book
					keyboard.append([InlineKeyboardButton(book.title, callback_data=f"teach_book_{book.id}")])

				reply_markup = InlineKeyboardMarkup(keyboard)

				await update.message.reply_text(
					"The best way to learn is to teach! Choose a book to practice explaining:",
					reply_markup=reply_markup
				)

			except Exception as e:
				logging.error(f"Error in send_teaching_prompt: {str(e)}")
				await update.message.reply_text("Sorry, there was an error preparing the teaching prompt.")
			finally:
				db.close()
		else:
			# Generate a teaching prompt based on the provided summary
			prompt = self.generate_prompt(summary)
			await update.message.reply_text(prompt)
			# Set context to awaiting teaching response
			context.user_data["awaiting_teaching"] = True

	async def handle_book_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles the selection of a book for teaching
		"""
		query = update.callback_query
		await query.answer()

		if query.data.startswith("teach_book_"):
			book_id = int(query.data.split("_")[2])
			user_id = update.effective_user.id

			db = SessionLocal()
			try:
				# Get the book summary
				summary = db.query("Summary").filter(
					"Summary.user_id" == user_id,
					"Summary.book_id" == book_id
				).order_by("Summary.created_at.desc()").first()

				if not summary:
					await query.edit_message_text(
						"Sorry, I couldn't find a summary for this book. "
						"Please summarize it first using /summary."
					)
					return

				# Generate a teaching prompt
				teaching_prompt = self.generate_prompt(summary.summary)

				# Store that we're waiting for a teaching response
				context.user_data["awaiting_teaching"] = True
				context.user_data["teaching_book_id"] = book_id

				await query.edit_message_text(teaching_prompt)

			except Exception as e:
				logging.error(f"Error in handle_book_selection: {str(e)}")
				await query.edit_message_text("Sorry, there was an error generating the teaching prompt.")
			finally:
				db.close()

	def generate_prompt(self, summary):
		"""
		Generates a teaching prompt based on the provided summary.
		"""
		try:
			prompt = f"""
            Based on the following summary, generate a teaching prompt that will help the user solidify their understanding.
            The prompt should ask them to explain a key concept from the summary in their own words.
            
            Summary: {summary}
            """

			response = self.model.generate_content(prompt)
			teaching_prompt = response.text.strip()

			# Add framing to the AI-generated prompt
			framed_prompt = (
				"👨‍🏫 *Teaching Challenge* 👨‍🏫\n\n"
				"Explaining concepts in your own words is one of the best ways to ensure you understand and remember them.\n\n"
				f"{teaching_prompt}\n\n"
				"Reply with your explanation, and I'll provide feedback on your understanding."
			)

			return framed_prompt

		except Exception as e:
			logging.error(f"Error generating teaching prompt: {str(e)}")
			return (
				"👨‍🏫 *Teaching Challenge* 👨‍🏫\n\n"
				"Explain one key concept from this book in your own words. "
				"What was the most important idea you learned, and how would you teach it to someone else?"
			)

async def handle_teaching_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""
	Handles the user's response to a teaching prompt
	"""
	if not context.user_data.get("awaiting_teaching"):
		return

	user_response = update.message.text
	book_id = context.user_data.get("teaching_book_id")
	user_id = update.effective_user.id

	# Remove the awaiting flag
	context.user_data.pop("awaiting_teaching", None)
	context.user_data.pop("teaching_book_id", None)

	# Initialize Gemini
	genai.configure(api_key=GENAI_API_KEY)
	model = genai.GenerativeModel('gemini-pro')

	try:
		# Get feedback on the user's explanation
		feedback_prompt = f"""
        The user was asked to explain a concept from a book in their own words.
        Here is their explanation:
        
        "{user_response}"
        
        Please provide encouraging, specific feedback on:
        1. How well they understood the concept
        2. How clearly they explained it
        3. Any suggestions for improvement
        
        Be supportive and positive, focusing mainly on what they did well.
        """

		feedback_response = model.generate_content(feedback_prompt)
		feedback = feedback_response.text.strip()

		# Send the feedback
		await update.message.reply_text(
			"✨ *Feedback on Your Explanation* ✨\n\n"
			f"{feedback}\n\n"
			"Teaching others is one of the best ways to solidify your own understanding. Great job!",
			parse_mode='Markdown'
		)

	except Exception as e:
		logging.error(f"Error generating teaching feedback: {str(e)}")
		await update.message.reply_text(
			"Thanks for your explanation! Teaching others is one of the best ways to learn."
		)