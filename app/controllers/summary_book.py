from telegram import Update
from telegram.ext import ContextTypes
from app.utils.file_processing import extract_text_from_pdf, extract_text_from_epub, extract_text_from_fb2
from app.utils.chunking import split_into_chunks
from app.services.summarization_service import summarize_with_gemini
from constants.constants import ERROR_MESSAGES

async def summarize_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	file = update.message.document
	file_path = f"./downloads/{file.file_name}"

	try:
		# Download the file
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

		await update.message.reply_text(f"Summary: {final_summary[:4096]}")  # Telegram message limit
	except Exception as e:
		await update.message.reply_text(ERROR_MESSAGES["API_ERROR"])