# app/services/reminders_service.py
import logging
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from app.database.db_handler import (
    SessionLocal,
    create_reminder,
    get_due_reminders,
    mark_reminder_sent,
    save_quiz_to_db
)
from app.services.summarization_service import summarize_with_gemini
from app.services.quiz_service import generate_quiz_questions

async def schedule_spaced_repetition(context, user_id, book_title):
    """
    Schedules spaced repetition reminders for a book.
    """
    # Get book_id from context.chat_data or from DB
    book_id = context.chat_data.get("current_book_id")

    if not book_id:
        logging.error(f"No book_id found for user {user_id} and book {book_title}")
        return

    # Define intervals for spaced repetition (in days)
    intervals = {
        "summary": [1, 3, 7, 30],  # Days to send summary reminders
        "quiz": [2, 5, 14],         # Days to send quiz questions
        "teaching": [4, 10, 21]     # Days to send teaching prompts
    }

    db = SessionLocal()
    try:
        # Schedule all reminders
        for reminder_type, days_list in intervals.items():
            for days in days_list:
                create_reminder(db, user_id, book_id, reminder_type, days)

        logging.info(f"Scheduled spaced repetition for user {user_id} and book {book_id}")
    except Exception as e:
        logging.error(f"Error scheduling reminders: {str(e)}")
    finally:
        db.close()

async def process_due_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    Processes reminders that are due to be sent.
    """
    db = SessionLocal()
    try:
        due_reminders = get_due_reminders(db)
        for reminder in due_reminders:
            user_book = reminder.user_book
            user_id = user_book.user_id
            book = user_book.book

            if reminder.reminder_type == "summary":
                await send_summary_reminder(context, user_id, book)
            elif reminder.reminder_type == "quiz":
                await send_quiz_reminder(context, user_id, book)
            elif reminder.reminder_type == "teaching":
                await send_teaching_reminder(context, user_id, book)

            # Mark reminder as sent
            mark_reminder_sent(db, reminder.id)

    except Exception as e:
        logging.error(f"Error processing reminders: {str(e)}")
    finally:
        db.close()

async def send_summary_reminder(context, user_id, book):
    """
    Sends a summary reminder.
    """
    try:
        # Get the latest summary for this book
        db = SessionLocal()
        summary = db.query("Summary").filter(
            "Summary.user_id" == user_id,
            "Summary.book_id" == book.id
        ).order_by("Summary.created_at.desc()").first()

        if not summary:
            logging.error(f"No summary found for user {user_id} and book {book.id}")
            return

        message = f"📚 Reminder for '{book.title}'\n\n"
        message += f"Here's a refresher of the key points:\n\n{summary.summary[:1000]}..."

        await context.bot.send_message(chat_id=user_id, text=message)
        logging.info(f"Sent summary reminder to user {user_id} for book {book.id}")

    except Exception as e:
        logging.error(f"Error sending summary reminder: {str(e)}")
    finally:
        db.close()

async def send_quiz_reminder(context, user_id, book):
    """
    Sends a quiz question as a reminder.
    """
    try:
        db = SessionLocal()
        # Get the summary for the book
        summary = db.query("Summary").filter(
            "Summary.user_id" == user_id,
            "Summary.book_id" == book.id
        ).order_by("Summary.created_at.desc()").first()

        if not summary:
            logging.error(f"No summary found for user {user_id} and book {book.id}")
            return

        # Generate quiz questions
        questions = generate_quiz_questions(summary.summary)
        if not questions or len(questions) == 0:
            logging.error(f"Failed to generate quiz questions for user {user_id} and book {book.id}")
            return

        # Pick the first question
        question = questions[0]

        # Save the quiz to the database
        quiz = save_quiz_to_db(db, user_id, book.id, question["question"], question["answer"])

        message = f"🧠 Quiz time for '{book.title}'!\n\n"
        message += f"Question: {question['question']}\n\n"
        message += "Reply with your answer, and I'll let you know if it's correct!"

        # Store the active quiz in the context
        context.chat_data["active_quiz"] = quiz.id

        await context.bot.send_message(chat_id=user_id, text=message)
        logging.info(f"Sent quiz reminder to user {user_id} for book {book.id}")

    except Exception as e:
        logging.error(f"Error sending quiz reminder: {str(e)}")
    finally:
        db.close()

async def send_teaching_reminder(context, user_id, book):
    """
    Sends a teaching prompt as a reminder.
    """
    try:
        db = SessionLocal()
        # Get the summary for the book
        summary = db.query("Summary").filter(
            "Summary.user_id" == user_id,
            "Summary.book_id" == book.id
        ).order_by("Summary.created_at.desc()").first()

        if not summary:
            logging.error(f"No summary found for user {user_id} and book {book.id}")
            return

        # Generate a teaching prompt
        prompt = f"Based on '{book.title}', explain the concept of {get_random_concept(summary.summary)} in your own words."

        message = f"👨‍🏫 Teaching moment for '{book.title}'!\n\n"
        message += "The best way to remember what you've learned is to teach it to someone else.\n\n"
        message += f"Prompt: {prompt}\n\n"
        message += "Reply with your explanation, and I'll provide feedback!"

        # Store that we're waiting for a teaching response
        context.chat_data["awaiting_teaching"] = True

        await context.bot.send_message(chat_id=user_id, text=message)
        logging.info(f"Sent teaching reminder to user {user_id} for book {book.id}")

    except Exception as e:
        logging.error(f"Error sending teaching reminder: {str(e)}")
    finally:
        db.close()

def get_random_concept(summary):
    """
    Extracts a random concept from the summary to use in a teaching prompt.
    """
    # This is a simplified version. In a real implementation, you would use NLP
    # to extract key concepts from the summary

    # For now, just use a generic prompt
    return "a key idea from this book"