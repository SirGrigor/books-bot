# app/services/nlp_service.py

import logging
import re
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from constants.constants import GENAI_API_KEY, GEMINI_MODEL_NAME
from app.utils.chunking import split_into_chunks

# Initialize the Gemini client
try:
	genai.configure(api_key=GENAI_API_KEY)
	logging.info("Google Generative AI client configured successfully")
except Exception as e:
	logging.error(f"Failed to configure Google Generative AI client: {str(e)}")

class NLPService:
	"""Service for advanced NLP functionality including text chunking, chapter detection, and content generation"""

	def __init__(self):
		self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
		logging.info(f"NLP Service initialized with model: {GEMINI_MODEL_NAME}")

	def detect_chapters(self, text: str) -> List[Dict]:
		"""
		Detects chapter boundaries in the text and returns a list of chapters
		Each chapter contains title, start_pos, end_pos, and content
		"""
		try:
			# First try to detect obvious chapter markers using regex
			chapter_pattern = re.compile(r'(?:chapter|section)\s+(?:[0-9]+|[IVXLCDM]+)(?:\s*[:.\-–—]\s*|\s+)([^\n]+)',
										 re.IGNORECASE)

			# If the book is too large, we need to process it in chunks
			if len(text) > 30000:
				# Initial chunking - rough text splits
				chunks = split_into_chunks(text, 30000)
				chapters = []

				for i, chunk in enumerate(chunks):
					# Try to find chapter boundaries using LLM
					chapter_data = self._extract_chapters_with_llm(chunk,
																   start_position=i * 30000)
					if chapter_data:
						chapters.extend(chapter_data)

				return self._refine_chapters(chapters, text)
			else:
				# For smaller books, process the entire text at once
				return self._extract_chapters_with_llm(text)
		except Exception as e:
			logging.error(f"Error detecting chapters: {str(e)}")
			# Fallback: treat the entire text as one chapter
			return [{"title": "Book Content", "start_pos": 0, "end_pos": len(text), "content": text}]

	def _extract_chapters_with_llm(self, text: str, start_position: int = 0) -> List[Dict]:
		"""Uses the Gemini model to identify chapter boundaries"""
		try:
			prompt = self._get_chapter_detection_prompt(text[:10000])  # Send first part for analysis
			response = self.model.generate_content(prompt)

			if not response or not hasattr(response, 'text'):
				logging.warning("Empty response from LLM for chapter detection")
				return []

			# Parse the chapter structure from the LLM response
			chapters = self._parse_chapter_response(response.text, text, start_position)
			return chapters
		except Exception as e:
			logging.error(f"Error in chapter extraction with LLM: {str(e)}")
			return []

	def _parse_chapter_response(self, response: str, text: str, offset: int = 0) -> List[Dict]:
		"""Parses the LLM response to extract chapter information"""
		chapters = []

		try:
			# Look for JSON-like or structured output in the response
			import json
			# Try to find a JSON array in the response
			matches = re.findall(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
			if matches:
				for match in matches:
					try:
						parsed_chapters = json.loads(match)
						if isinstance(parsed_chapters, list):
							for ch in parsed_chapters:
								if 'title' in ch and ('start_marker' in ch or 'start_text' in ch):
									# Find actual positions in the text
									start_marker = ch.get('start_marker') or ch.get('start_text')
									end_marker = ch.get('end_marker') or ch.get('end_text')

									start_pos = text.find(start_marker)
									if start_pos == -1:
										continue

									if end_marker:
										end_pos = text.find(end_marker, start_pos + 1)
										if end_pos == -1:
											end_pos = len(text)
									else:
										end_pos = len(text)

									chapter_content = text[start_pos:end_pos]
									chapters.append({
										"title": ch['title'],
										"start_pos": start_pos + offset,
										"end_pos": end_pos + offset,
										"content": chapter_content
									})
					except json.JSONDecodeError:
						continue

			# If no structured data found, try regex-based parsing
			if not chapters:
				# Look for chapter titles with positions
				chapter_entries = re.findall(r'Chapter:?\s+([^\n]+)\s+Start:?\s+([^\n]+)\s+End:?\s+([^\n]+)',
											 response, re.IGNORECASE)

				for title, start_text, end_text in chapter_entries:
					title = title.strip()
					start_text = start_text.strip()
					end_text = end_text.strip()

					start_pos = text.find(start_text)
					if start_pos == -1:
						continue

					end_pos = text.find(end_text, start_pos + 1)
					if end_pos == -1:
						end_pos = len(text)

					chapter_content = text[start_pos:end_pos]
					chapters.append({
						"title": title,
						"start_pos": start_pos + offset,
						"end_pos": end_pos + offset,
						"content": chapter_content
					})
		except Exception as e:
			logging.error(f"Error parsing chapter response: {str(e)}")

		# If all else fails, create a single chapter
		if not chapters:
			chapters.append({
				"title": "Content Section",
				"start_pos": offset,
				"end_pos": offset + len(text),
				"content": text
			})

		return chapters

	def _refine_chapters(self, chapters: List[Dict], full_text: str) -> List[Dict]:
		"""Refines chapter boundaries and titles"""
		# Sort chapters by start position
		chapters = sorted(chapters, key=lambda x: x['start_pos'])

		# Adjust end positions to prevent overlaps
		for i in range(len(chapters) - 1):
			if chapters[i]['end_pos'] > chapters[i+1]['start_pos']:
				chapters[i]['end_pos'] = chapters[i+1]['start_pos']
				chapters[i]['content'] = full_text[chapters[i]['start_pos']:chapters[i]['end_pos']]

		return chapters

	def summarize_chapter(self, chapter_text: str, chapter_title: str = "") -> str:
		"""Generate a concise summary of a chapter"""
		try:
			prompt = self._get_chapter_summary_prompt(chapter_text, chapter_title)
			response = self.model.generate_content(prompt)

			if response and hasattr(response, 'text'):
				return response.text
			return "Summary could not be generated."
		except Exception as e:
			logging.error(f"Error summarizing chapter: {str(e)}")
			return "Error generating summary."

	def generate_quiz_questions(self, chapter_text: str, num_questions: int = 3) -> List[Dict]:
		"""Generate quiz questions based on the chapter content"""
		try:
			prompt = self._get_quiz_generation_prompt(chapter_text, num_questions)
			response = self.model.generate_content(prompt)

			if not response or not hasattr(response, 'text'):
				return []

			# Parse the quiz questions
			return self._parse_quiz_response(response.text)
		except Exception as e:
			logging.error(f"Error generating quiz questions: {str(e)}")
			return []

	def _parse_quiz_response(self, response: str) -> List[Dict]:
		"""Parse the quiz generation response to extract questions and answers"""
		questions = []

		try:
			import json
			# Try to find JSON in the response
			matches = re.findall(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
			if matches:
				for match in matches:
					try:
						parsed_questions = json.loads(match)
						if isinstance(parsed_questions, list):
							for q in parsed_questions:
								if 'question' in q and 'answer' in q:
									questions.append({
										'question': q['question'],
										'answer': q['answer']
									})
					except json.JSONDecodeError:
						continue

			# If no structured data found, try regex-based parsing
			if not questions:
				# Look for Q&A patterns
				qa_pairs = re.findall(r'(?:Question|Q):\s*([^\n]+)\s*(?:Answer|A):\s*([^\n]+)',
									  response, re.IGNORECASE | re.DOTALL)

				for question, answer in qa_pairs:
					questions.append({
						'question': question.strip(),
						'answer': answer.strip()
					})
		except Exception as e:
			logging.error(f"Error parsing quiz response: {str(e)}")

		return questions

	def generate_teaching_prompt(self, chapter_text: str) -> str:
		"""Generate a teaching prompt to help the user explain the concept"""
		try:
			prompt = self._get_teaching_prompt(chapter_text)
			response = self.model.generate_content(prompt)

			if response and hasattr(response, 'text'):
				return response.text
			return "Explain a key concept from this chapter in your own words."
		except Exception as e:
			logging.error(f"Error generating teaching prompt: {str(e)}")
			return "Explain a key concept from this chapter in your own words."

	def generate_retention_reminder(self, chapter_summary: str, stage: int) -> str:
		"""
		Generate a retention reminder for spaced repetition
		stage: 1=1day, 2=3days, 3=7days, 4=30days
		"""
		try:
			prompt = self._get_reminder_prompt(chapter_summary, stage)
			response = self.model.generate_content(prompt)

			if response and hasattr(response, 'text'):
				return response.text
			return f"Here's a reminder of what you learned: {chapter_summary[:100]}..."
		except Exception as e:
			logging.error(f"Error generating reminder: {str(e)}")
			return f"Here's a reminder of what you learned: {chapter_summary[:100]}..."

	# Prompt templates
	def _get_chapter_detection_prompt(self, text_sample: str) -> str:
		"""Returns a prompt for chapter detection"""
		return f"""Analyze the following book text and identify chapter boundaries.
For each chapter, provide:
1. The chapter title
2. The text that marks the beginning of the chapter
3. The text that marks the end of the chapter (or leave blank if it's the end of the provided text)

Format your response as a JSON array of objects with 'title', 'start_marker', and 'end_marker' fields.

Sample text:
{text_sample[:5000]}...

Output the JSON array only, without any additional explanation."""

	def _get_chapter_summary_prompt(self, chapter_text: str, chapter_title: str) -> str:
		"""Returns a prompt for chapter summarization"""
		title_context = f" titled '{chapter_title}'" if chapter_title else ""
		return f"""Summarize the following chapter{title_context} in a concise way. Focus on:
1. Main ideas and key concepts
2. Important insights
3. Practical takeaways

Make the summary engaging and easy to understand. Keep it to around 3-5 paragraphs.

Chapter text:
{chapter_text[:10000]}..."""

	def _get_quiz_generation_prompt(self, chapter_text: str, num_questions: int) -> str:
		"""Returns a prompt for quiz question generation"""
		return f"""Based on the following chapter text, create {num_questions} quiz questions that test understanding of key concepts.
For each question, provide the correct answer.

Format your response as a JSON array of objects, where each object has 'question' and 'answer' fields.

Chapter text:
{chapter_text[:8000]}...

Output the JSON array only, without any additional explanation."""

	def _get_teaching_prompt(self, chapter_text: str) -> str:
		"""Returns a prompt for generating teaching challenges"""
		return f"""Create a teaching prompt that will help someone solidify their understanding of the following text.
The teaching prompt should ask them to explain a key concept from the text in their own words.
Make it specific enough that they can focus on a particular idea, but open enough that it requires understanding rather than memorization.

Chapter text:
{chapter_text[:8000]}...

Return just the teaching prompt without any additional explanation."""

	def _get_reminder_prompt(self, summary: str, stage: int) -> str:
		"""Returns a prompt for generating spaced repetition reminders"""
		stage_descriptions = {
			1: "This is the first reminder (1 day after learning). Keep it encouraging and reinforce the key points.",
			2: "This is the second reminder (3 days after learning). Include some simple recall questions.",
			3: "This is the third reminder (1 week after learning). Focus on application of concepts.",
			4: "This is the fourth reminder (1 month after learning). Create a comprehensive review."
		}

		stage_desc = stage_descriptions.get(stage, "This is a learning reminder.")

		return f"""Create a spaced repetition reminder based on the following summary of a book chapter.
{stage_desc}

Original summary:
{summary}

Make the reminder concise, engaging, and focused on retention. Include 1-2 questions that promote active recall.
Return just the reminder content without any additional explanation."""