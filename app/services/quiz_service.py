# app/services/quiz_service.py
import os
import logging
import google.generativeai as genai
from constants.constants import GENAI_API_KEY
import json
import re

# Initialize the Gemini client
genai.configure(api_key=GENAI_API_KEY)

def generate_quiz_questions(text, num_questions=3):
	"""
	Generates quiz questions based on the provided text.
	Returns a list of dictionaries, each containing a question and its answer.
	"""
	try:
		model = genai.GenerativeModel('gemini-pro')

		prompt = f"""
        Based on the following text, generate {num_questions} quiz questions that test understanding of key concepts.
        For each question, provide the correct answer.
        Format your response as a JSON array of objects, where each object has 'question' and 'answer' fields.
        
        Text: {text[:1500]}  # Limit text to avoid hitting model token limits
        """

		response = model.generate_content(prompt)
		response_text = response.text

		# Parse the response to extract questions and answers
		questions = []

		try:
			# Try to parse the JSON response
			# Look for JSON pattern in the response
			json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
			if json_match:
				json_str = json_match.group(0)
				questions = json.loads(json_str)
			else:
				# If structured parsing fails, try a simple parse approach
				# This is a fallback in case the AI doesn't format as requested
				lines = response_text.split('\n')
				current_question = None
				current_answer = None

				for line in lines:
					if line.startswith("Question:") or line.startswith("Q:"):
						# Save the previous question if exists
						if current_question and current_answer:
							questions.append({
								"question": current_question,
								"answer": current_answer
							})
						current_question = line.split(":", 1)[1].strip()
						current_answer = None
					elif line.startswith("Answer:") or line.startswith("A:"):
						current_answer = line.split(":", 1)[1].strip()

				# Add the last question
				if current_question and current_answer:
					questions.append({
						"question": current_question,
						"answer": current_answer
					})
		except Exception as parsing_error:
			logging.error(f"Error parsing quiz questions: {str(parsing_error)}")

		# If all parsing failed, create default questions based on text
		if not questions:
			# Extract some words to create basic questions
			words = re.findall(r'\b\w{4,}\b', text)
			important_words = [word for word in words if word.lower() not in
							   ['this', 'that', 'there', 'their', 'about', 'would', 'could', 'should']]

			# Take a few unique words for questions
			unique_words = list(set(important_words))[:3]

			for word in unique_words:
				questions.append({
					"question": f"What is the significance of '{word}' in this text?",
					"answer": f"This requires reflecting on how '{word}' is used in the context of the text."
				})

			# If still no questions, add one generic question
			if not questions:
				questions = [{
					"question": "What is one of the key concepts discussed in this text?",
					"answer": "This question requires reflection on the key concepts in the text."
				}]

		return questions

	except Exception as e:
		logging.error(f"Error generating quiz questions: {str(e)}")
		# Return a fallback question if everything fails
		return [{
			"question": "What was the main idea presented in this text?",
			"answer": "The main idea relates to the central concept discussed in the text."
		}]