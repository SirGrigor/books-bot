# app/services/reminders_service.py
import logging
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from app.database.db_handler import (
    SessionLocal,
    create_reminder,
    get_due_reminders,
    mark_reminder_sent,
    Book,
    Summary,
    UserBook,
    Reminder
)

async def schedule_spaced_repetition(context, user_id, book_title):
    """
    Schedules spaced repetition reminders for a book.
    """
    # Get book_id from context or look it up in the DB
    book_id = context.chat_data.get("current_book_id")

    if not book_id:
        # Try to look up the book ID by title
        db = SessionLocal()
        try:
            book = db.query(Book).filter(Book.title == book_title).first()
            if book:
                book_id = book.id
            else:
                logging.error(f"No book found with title {book_title}")
                return
        except Exception as e:
            logging.error(f"Error looking up book: {str(e)}")
            return
        finally:
            db.close()

    if not book_id:
        logging.error(f"Could not determine book_id for user {user_id} and book {book_title}")
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
    This is called on a schedule by the job queue.
    """
    logging.info("Processing due reminders...")

    db = SessionLocal()
    try:
        due_reminders = get_due_reminders(db)
        logging.info(f"Found {len(due_reminders)} due reminders")

        for reminder in due_reminders:
            try:
                # Get the user-book relationship
                user_book = db.query(UserBook).filter(UserBook.id == reminder.user_book_id).first()

                if not user_book:
                    logging.error(f"UserBook not found for reminder {reminder.id}")
                    continue

                user_id = user_book.user_id
                book_id = user_book.book_id

                # Get the book
                book = db.query(Book).filter(Book.id == book_id).first()

                if not book:
                    logging.error(f"Book not found for reminder {reminder.id}")
                    continue

                # Send the appropriate reminder based on type
                if reminder.reminder_type == "summary":
                    await send_summary_reminder(context, user_id, book, db)
                elif reminder.reminder_type == "quiz":
                    await send_quiz_reminder(context, user_id, book, db)
                elif reminder.reminder_type == "teaching":
                    await send_teaching_reminder(context, user_id, book, db)

                # Mark reminder as sent
                mark_reminder_sent(db, reminder.id)
                logging.info(f"Sent {reminder.reminder_type} reminder for book '{book.title}' to user {user_id}")

            except Exception as e:
                logging.error(f"Error processing reminder {reminder.id}: {str(e)}")
                continue

    except Exception as e:
        logging.error(f"Error processing reminders: {str(e)}")
    finally:
        db.close()

async def send_summary_reminder(context, user_id, book, db):
    """
    Sends a summary reminder.
    """
    try:
        # Get the summary for this book
        summary = db.query(Summary).filter(
            Summary.user_id == str(user_id),
            Summary.book_id == book.id
        ).order_by(Summary.id.desc()).first()

        summary_text = "No summary available yet."
        if summary:
            # Truncate the summary to a reasonable length
            summary_text = summary.summary[:1000]
            if len(summary.summary) > 1000:
                summary_text += "..."

        message = f"📚 Reminder for '{book.title}'\n\n"
        message += f"Here's a refresher of the key points:\n\n{summary_text}\n\n"
        message += "Reviewing this information at spaced intervals will help you retain it better!"

        await context.bot.send_message(chat_id=user_id, text=message)

    except Exception as e:
        logging.error(f"Error sending summary reminder: {str(e)}")
        raise

async def send_quiz_reminder(context, user_id, book, db):
    """
    Sends a quiz reminder.
    """
    try:
        # Get the summary for this book
        summary = db.query(Summary).filter(
            Summary.user_id == str(user_id),
            Summary.book_id == book.id
        ).order_by(Summary.id.desc()).first()

        if not summary:
            message = f"🧠 Quiz time for '{book.title}'!\n\n"
            message += "I don't have a summary for this book yet, so I can't generate quiz questions. "
            message += "Try uploading a summary first!"

            await context.bot.send_message(chat_id=user_id, text=message)
            return

        # Generate a simple quiz question based on the summary
        # In a real implementation, you would use the quiz_service here
        question = f"What is one of the key concepts discussed in '{book.title}'?"

        message = f"🧠 Quiz time for '{book.title}'!\n\n"
        message += f"Question: {question}\n\n"
        message += "Reply with your answer, and I'll provide feedback!"

        # We'd normally store this in the database, but for simplicity:
        if not context.user_data:
            context.user_data = {}
        context.user_data["awaiting_quiz_answer"] = True

        await context.bot.send_message(chat_id=user_id, text=message)

    except Exception as e:
        logging.error(f"Error sending quiz reminder: {str(e)}")
        raise

async def send_teaching_reminder(context, user_id, book, db):
    """
    Sends a teaching prompt reminder.
    """
    try:
        # Get the summary for this book
        summary = db.query(Summary).filter(
            Summary.user_id == str(user_id),
            Summary.book_id == book.id
        ).order_by(Summary.id.desc()).first()

        if not summary:
            message = f"👨‍🏫 Teaching moment for '{book.title}'!\n\n"
            message += "I don't have a summary for this book yet, so I can't generate a teaching prompt. "
            message += "Try uploading a summary first!"

            await context.bot.send_message(chat_id=user_id, text=message)
            return

        # Generate a simple teaching prompt
        prompt = f"Explain in your own words what '{book.title}' is about and what you learned from it."

        message = f"👨‍🏫 Teaching moment for '{book.title}'!\n\n"
        message += "The best way to remember what you've learned is to teach it to someone else.\n\n"
        message += f"Prompt: {prompt}\n\n"
        message += "Reply with your explanation, and I'll provide feedback!"

        # We'd normally store this in the database, but for simplicity:
        if not context.user_data:
            context.user_data = {}
        context.user_data["awaiting_teaching"] = True

        await context.bot.send_message(chat_id=user_id, text=message)

    except Exception as e:
        logging.error(f"Error sending teaching reminder: {str(e)}")
        raise