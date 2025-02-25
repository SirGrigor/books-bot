from telegram import Update
from telegram.ext import ContextTypes

class TeachingController:
	def __init__(self, teaching_service):
		self.teaching_service = teaching_service

	async def send_teaching_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, summary: str):
		"""
		Sends a teaching prompt based on the provided summary.
		"""
		prompt = self.teaching_service.generate_prompt(summary)
		await update.message.reply_text(prompt)