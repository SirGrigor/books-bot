from telegram import Update
from telegram.ext import ContextTypes
from app.services.summarization_service import summarize_with_gemini
from constants.constants import ERROR_MESSAGES

async def summarize_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_input = update.message.text
	if len(user_input.split()) < 10:
		await update.message.reply_text(ERROR_MESSAGES["INVALID_INPUT"])
		return
	try:
		summary = summarize_with_gemini(user_input)
		await update.message.reply_text(f"Summary: {summary}")
	except Exception as e:
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])