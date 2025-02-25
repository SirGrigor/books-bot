# app/services/teaching_service.py
import os

import google.generativeai as genai

genai.configure(api_key=os.getenv("GENAI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')


def generate_discussion_prompt(text):
	"""
	Generates discussion prompts based on the input text.
	"""
	prompt = f"Generate thought-provoking questions about the following text: {text}"
	response = model.generate_content(prompt)
	return response.text
