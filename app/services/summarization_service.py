# app/services/summarization_service.py
import os
import google.generativeai as genai
from app.utils.chunking import split_into_chunks

# Initialize the Gemini client
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def summarize_large_text(text):
	"""
	Summarizes large text by splitting it into chunks.
	"""
	chunks = split_into_chunks(text)
	summaries = []
	for chunk in chunks:
		summary = summarize_with_gemini(chunk)  # Use Gemini for summarization
		summaries.append(summary)
	return " ".join(summaries)

def summarize_with_gemini(text):
	try:
		model = genai.GenerativeModel('gemini-2.0-flash')
		response = model.generate_content(f"Summarize this: {text}")
		return response.text
	except Exception as e:
		raise RuntimeError(f"Error during summarization: {str(e)}")