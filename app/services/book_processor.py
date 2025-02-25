# app/services/book_processor.py

import logging
import os
from typing import List, Dict, Optional, Tuple
from app.services.nlp_service import NLPService
from app.utils.chunking import split_into_chunks, split_by_chapters, extract_semantic_chunks
from app.database.db_handler import (
	SessionLocal,
	save_summary_to_db,
	save_quiz_to_db,
	create_reminder
)
from app.utils.file_processing import extract_text_from_pdf, extract_text_from_epub, extract_text_from_fb2
from constants.constants import SPACED_REPETITION_INTERVALS

class BookProcessor:
	"""
	Processes book content for optimal learning and retention.
	Handles book chunking, chapter detection, summarization, and
	generating learning materials like quizzes and teaching prompts.
	"""

	def __init__(self):
		self.nlp_service = NLPService()
		logging.info("Book Processor initialized")

	async def process_uploaded_book(self, file_path: str, user_id: str, book_id: Optional[int] = None) -> Dict:
		"""
		Processes an uploaded book file and generates all necessary learning materials

		Args:
			file_path: Path to the book file
			user_id: Telegram user ID
			book_id: Optional book ID if already in database

		Returns:
			Dictionary with processing results
		"""
		try:
			# Extract text based on file type
			logging.info(f"Processing book file: {file_path}")

			if file_path.endswith(".pdf"):
				full_text = extract_text_from_pdf(file_path)
			elif file_path.endswith(".epub"):
				full_text = extract_text_from_epub(file_path)
			elif file_path.endswith(".fb2"):
				full_text = extract_text_from_fb2(file_path)
			else:
				return {"success": False, "error": "Unsupported file type"}

			if not full_text or len(full_text.strip()) < 100:
				return {"success": False, "error": "Could not extract text from file"}

			logging.info(f"Successfully extracted {len(full_text)} characters from file")

			# Process the book content
			result = await self.process_book_content(full_text, user_id, book_id)

			# Clean up the file
			try:
				os.remove(file_path)
				logging.info(f"Removed temporary file: {file_path}")
			except Exception as e:
				logging.warning(f"Failed to remove temporary file: {str(e)}")

			return result

		except Exception as e:
			logging.error(f"Error processing book: {str(e)}")
			return {"success": False, "error": str(e)}

	async def process_book_content(self, text: str, user_id: str, book_id: Optional[int] = None) -> Dict:
		"""
		Processes book content text and generates all necessary learning materials

		Args:
			text: Full book text
			user_id: Telegram user ID
			book_id: Optional book ID if already in database

		Returns:
			Dictionary with processing results
		"""
		try:
			db = SessionLocal()
			processing_results = {"success": True, "chapters": []}

			try:
				# Step 1: Detect chapters
				logging.info("Detecting chapters in book content")
				chapters = self.nlp_service.detect_chapters(text)

				# Step 2: Process each chapter
				for i, chapter in enumerate(chapters):
					chapter_title = chapter.get("title", f"Chapter {i+1}")
					chapter_text = chapter.get("content", "")

					# Generate chapter summary
					summary = self.nlp_service.summarize_chapter(chapter_text, chapter_title)

					# Save the summary to database
					db_summary = save_summary_to_db(
						db,
						user_id,
						title=chapter_title,
						original_text=chapter_text,
						summary=summary,
						book_id=book_id
					)

					# Generate quiz questions
					quiz_questions = self.nlp_service.generate_quiz_questions(chapter_text)

					# Save quiz questions to database
					quiz_ids = []
					for quiz_item in quiz_questions:
						quiz = save_quiz_to_db(
							db,
							user_id,
							book_id,
							quiz_item["question"],
							quiz_item["answer"]
						)
						quiz_ids.append(quiz.id)

					# Schedule reminders for this chapter if book_id is provided
					reminder_ids = []
					if book_id:
						for reminder_type, days_list in SPACED_REPETITION_INTERVALS.items():
							for days in days_list:
								reminder = create_reminder(db, user_id, book_id, reminder_type, days)
								reminder_ids.append(reminder.id)

					# Add chapter result to processing results
					processing_results["chapters"].append({
						"title": chapter_title,
						"summary": summary,
						"summary_id": db_summary.id if db_summary else None,
						"quiz_count": len(quiz_questions),
						"quiz_ids": quiz_ids,
						"reminder_ids": reminder_ids
					})

					logging.info(f"Processed chapter: {chapter_title}")

				# Add overall book processing info
				processing_results["total_chapters"] = len(chapters)
				processing_results["book_id"] = book_id

				logging.info(f"Successfully processed book with {len(chapters)} chapters")
				return processing_results

			except Exception as e:
				logging.error(f"Error during book processing: {str(e)}")
				db.rollback()
				return {"success": False, "error": str(e)}
			finally:
				db.close()

		except Exception as e:
			logging.error(f"Error setting up book processing: {str(e)}")
			return {"success": False, "error": str(e)}

	async def generate_initial_summary(self, book_id: int, user_id: str) -> str:
		"""
		Generates an initial overall book summary for a newly selected book

		Args:
			book_id: Book ID
			user_id: Telegram user ID

		Returns:
			A concise overall summary of the book
		"""
		db = SessionLocal()
		try:
			# Get book information
			from app.database.db_handler import Book
			book = db.query(Book).filter(Book.id == book_id).first()

			if not book:
				return "Could not find book information."

			# For books in the curated list, we generate a comprehensive summary
			if book.is_recommended:
				# Generate a prompt for book summary
				prompt = f"""Provide a concise, comprehensive summary of the book '{book.title}' 
                {f'by {book.author}' if book.author else ''}. Focus on key concepts, major themes, 
                and practical takeaways. Make it engaging and informative (around 4-5 paragraphs)."""

				try:
					summary = self.nlp_service.model.generate_content(prompt).text

					# Save the summary
					save_summary_to_db(
						db,
						user_id,
						title=f"Overview: {book.title}",
						original_text=book.description or "",
						summary=summary,
						book_id=book_id
					)

					return summary
				except Exception as e:
					logging.error(f"Error generating initial summary: {str(e)}")
					# Fallback to description
					return book.description or f"You've selected '{book.title}'. Upload the book file to get a detailed summary."
			else:
				# For custom books, we use the description or provide instructions
				return book.description or f"You've selected '{book.title}'. Upload the book file to get a detailed summary."
		except Exception as e:
			logging.error(f"Error in generate_initial_summary: {str(e)}")
			return "An error occurred while generating the book summary."
		finally:
			db.close()

	async def generate_retention_reminder(self, reminder_type: str, book_id: int, user_id: str, stage: int) -> str:
		"""
		Generates a retention reminder based on type and spaced repetition stage

		Args:
			reminder_type: Type of reminder ('summary', 'quiz', 'teaching')
			book_id: Book ID
			user_id: Telegram user ID
			stage: Spaced repetition stage (1-4)

		Returns:
			Formatted reminder text
		"""
		db = SessionLocal()
		try:
			# Get the most recent summary for this book
			from app.database.db_handler import Summary
			summary = db.query(Summary).filter(
				Summary.user_id == str(user_id),
				Summary.book_id == book_id
			).order_by(Summary.id.desc()).first()

			if not summary:
				return "I don't have any summary information for this book yet."

			if reminder_type == "summary":
				# Generate a summary reminder
				return self.nlp_service.generate_retention_reminder(summary.summary, stage)

			elif reminder_type == "quiz":
				# Generate quiz questions
				quiz_questions = self.nlp_service.generate_quiz_questions(summary.summary, 2)

				if not quiz_questions:
					return "I couldn't generate quiz questions for this book. Try uploading a summary first."

				# Format the questions
				quiz_text = "📝 Quiz Time! Let's test your knowledge:\n\n"
				for i, q in enumerate(quiz_questions):
					quiz_text += f"{i+1}. {q['question']}\n\n"

				quiz_text += "Reply with your answers, and I'll provide feedback!"
				return quiz_text

			elif reminder_type == "teaching":
				# Generate a teaching prompt
				teaching_prompt = self.nlp_service.generate_teaching_prompt(summary.summary)

				teaching_text = "👨‍🏫 Teaching Challenge!\n\n"
				teaching_text += "The best way to reinforce your learning is to explain concepts to others.\n\n"
				teaching_text += f"{teaching_prompt}\n\n"
				teaching_text += "Reply with your explanation, and I'll provide feedback!"

				return teaching_text

			else:
				return "Unknown reminder type."

		except Exception as e:
			logging.error(f"Error generating retention reminder: {str(e)}")
			return "I couldn't generate a reminder for this book. Try uploading a summary first."
		finally:
			db.close()