# app/services/quiz_service.py
import os
import logging
import google.generativeai as genai
from constants.constants import GENAI_API_KEY

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
        
        Text: {text}
        """

		response = model.generate_content(prompt)
		response_text = response.text

		# Parse the response to extract questions and answers
		# This is a simplified approach - in a real implementation,
		# you would parse the JSON properly

		# For demonstration purposes, let's return a default set of questions
		# In a real implementation, you would parse the AI response

		questions = []
		for i in range(num_questions):
			questions.append({
				"question": f"Question {i + 1}",
				"answer": f"Answer {i + 1}"
			})

		return questions

	except Exception as e:
		logging.error(f"Error generating quiz questions: {str(e)}")
		return []