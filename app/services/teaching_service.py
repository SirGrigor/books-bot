# app/services/teaching_service.py
import logging
import os

try:
	import google.generativeai as genai
	from constants.constants import GENAI_API_KEY
	# Initialize the Gemini client
	genai.configure(api_key=GENAI_API_KEY)
except ImportError:
	logging.warning("Google Generative AI module not available.")
except Exception as e:
	logging.error(f"Error configuring Google Generative AI: {str(e)}")

def generate_discussion_prompt(text=None):
	"""
	Generates discussion prompts based on the input text.
	Falls back to generic prompts if AI generation fails.
	"""
	# Default generic prompts if generation fails
	generic_prompts = [
		"What was the most important concept you learned from this book?",
		"How could you apply the ideas from this book in your daily life?",
		"If you had to explain the main idea of this book to someone, what would you say?",
		"What surprised you the most about what you learned in this book?",
		"How has this book changed your perspective on the topic?"
	]

	# If no text provided, return a generic prompt
	if not text:
		import random
		return random.choice(generic_prompts)

	try:
		# Try to use Gemini AI to generate a prompt
		model = genai.GenerativeModel('gemini-pro')
		prompt = f"Generate a thought-provoking question about the following text that would help someone understand and remember the key concepts better: {text[:1000]}"

		response = model.generate_content(prompt)
		generated_prompt = response.text.strip()

		# If we got a reasonable response, use it
		if generated_prompt and len(generated_prompt) > 10:
			return generated_prompt
		else:
			import random
			return random.choice(generic_prompts)

	except Exception as e:
		logging.error(f"Error generating discussion prompt: {str(e)}")
		# Fall back to a generic prompt
		import random
		return random.choice(generic_prompts)