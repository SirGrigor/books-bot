import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database.db_handler import SummaryModel

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	handlers=[
		logging.FileHandler("bot.log"),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

class SummaryTextController:
	def __init__(self, summarizer, db_handler, teaching_service):
		self.summarizer = summarizer
		self.db_handler = db_handler
		self.teaching_service = teaching_service

	async def summary_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""
		Handles summarization of short text inputs.
		"""
		logger.info("Received /summary command from user.")
		if update.message is None:
			logger.warning("No message found in /summary command.")
			return

		text = " ".join(context.args)
		if not text:
			logger.info("User did not provide text for summarization.")
			await update.message.reply_text(
				"Please provide text to summarize. Example: /summary This is the text to summarize."
			)
			return

		status_message = await update.message.reply_text("Generating summary... Please wait.")
		logger.info(f"Generating summary for text: {text}")

		try:
			summary = self.summarizer.generate_summary(text)
			await status_message.edit_text("Summary generated successfully!")
			await update.message.reply_text(f"Summary: {summary}")
			logger.info(f"Generated summary: {summary}")

			user_id = str(update.effective_user.id)
			summary_model = SummaryModel(user_id=user_id, title="Short Text", summary=summary)
			self.db_handler.save_summary(summary_model)
			logger.info(f"Saved summary to database for user {user_id}.")

			prompt = self.teaching_service.generate_prompt(summary)
			await update.message.reply_text(prompt)
			logger.info(f"Sent teaching prompt: {prompt}")
		except Exception as e:
			logger.error(f"Error during summarization: {e}", exc_info=True)
			await status_message.edit_text("An error occurred while generating the summary. Please try again later.")