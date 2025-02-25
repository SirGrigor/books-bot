# app/services/reminders_service.py - ENHANCED

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
from app.services.book_processor import BookProcessor
from constants.constants import SPACED_REPETITION_INTERVALS

async def schedule_spaced_repetition(context, user_id, book_title):
    """
    Schedules spaced repetition reminders for a book using advanced intervals.
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

    db = SessionLocal()
    try:
        # Schedule reminders using the intervals from constants
        for reminder_type, days_list in SPACED_REPETITION_INTERVALS.items():
            for i, days in enumerate(days_list):
                # The stage is the index + 1 (stages 1-4)
                stage = i + 1
                create_reminder(db, user_id, book_id, reminder_type, days, stage)

        logging.info(f"Scheduled advanced spaced repetition for user {user_id} and book {book_id}")
    except Exception as e:
        logging.error(f"Error scheduling reminders: {str(e)}")
    finally:
        db.close()

async def process_due_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    Processes reminders that are due to be sent with enhanced content generation.
    This is called on a schedule by the job queue.
    """
    logging.info("Processing due reminders...")

    db = SessionLocal()
    try:
        due_reminders = get_due_reminders(db)
        logging.info(f"Found {len(due_reminders)} due reminders")

        # Initialize book processor for content generation
        book_processor = BookProcessor()

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

                # Generate reminder content based on type and stage
                reminder_content = await book_processor.generate_retention_reminder(
                    reminder.reminder_type,
                    book_id,
                    user_id,
                    reminder.stage
                )

                # Format the reminder message based on type
                message_prefix = {
                    "summary": "📚 Book Reminder",
                    "quiz": "🧠 Quiz Time",
                    "teaching": "👨‍🏫 Teaching Challenge"
                }.get(reminder.reminder_type, "📝 Learning Reminder")

                message = f"{message_prefix}: *{book.title}*\n\n{reminder_content}"

                # Send the reminder
                await context.bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

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

def create_reminder(db, user_id, book_id, reminder_type, days_ahead, stage=1):
    """
    Creates a spaced repetition reminder with a specified stage.
    """
    try:
        # Get the user-book relationship
        user_book = db.query(UserBook).filter(
            UserBook.user_id == str(user_id),
            UserBook.book_id == book_id
        ).first()

        if not user_book:
            raise ValueError("User-book relationship not found")

        # Create the reminder
        scheduled_for = datetime.utcnow() + timedelta(days=days_ahead)
        reminder = Reminder(
            user_book_id=user_book.id,
            reminder_type=reminder_type,
            scheduled_for=scheduled_for,
            stage=stage  # Add the stage information
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        return reminder
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating reminder: {str(e)}")
        raise