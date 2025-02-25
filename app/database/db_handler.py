# app/database/db_handler.py
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from constants.constants import DATABASE_URL
from app.database.models import Base, User, Message, Summary, Book, UserBook, Reminder, Quiz

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Function to save user metadata - already exists
def save_user_to_db(db, user_id, username, first_name):
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        db_user = User(user_id=user_id, username=username, first_name=first_name)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user

# Function to save a message - already exists
def save_message_to_db(db, user_id, message_text):
    db_message = Message(user_id=user_id, message_text=message_text)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Function to save a summary - already exists, updated to link to book
def save_summary_to_db(db, user_id, title, original_text, summary, book_id=None):
    db_summary = Summary(
        user_id=user_id,
        title=title,
        original_text=original_text,
        summary=summary,
        book_id=book_id
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

# New functions for book management

def get_recommended_books(db):
    """
    Retrieves the list of curated recommended books.
    """
    return db.query(Book).filter(Book.is_recommended == True).all()

def add_custom_book_to_db(db, title, user_id, author=None, description=None):
    """
    Adds a custom book to the database.
    """
    # Check if book already exists
    existing_book = db.query(Book).filter(Book.title == title).first()

    if existing_book:
        book = existing_book
    else:
        # Create new book
        book = Book(
            title=title,
            author=author,
            description=description,
            is_recommended=False
        )
        db.add(book)
        db.commit()
        db.refresh(book)

    # Create user-book relationship
    user_book = UserBook(
        user_id=user_id,
        book_id=book.id,
        started_at=datetime.utcnow()
    )
    db.add(user_book)
    db.commit()
    db.refresh(user_book)

    return book

def save_book_selection_to_db(db, user_id, book_id):
    """
    Saves a user's book selection.
    """
    # Get the book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise ValueError("Book not found")

    # Check if user already has this book
    existing_user_book = db.query(UserBook).filter(
        UserBook.user_id == user_id,
        UserBook.book_id == book_id
    ).first()

    if existing_user_book:
        user_book = existing_user_book
    else:
        user_book = UserBook(
            user_id=user_id,
            book_id=book_id,
            started_at=datetime.utcnow()
        )
        db.add(user_book)
        db.commit()
        db.refresh(user_book)

    return book

def create_reminder(db, user_id, book_id, reminder_type, days_ahead):
    """
    Creates a spaced repetition reminder.
    """
    # Get the user-book relationship
    user_book = db.query(UserBook).filter(
        UserBook.user_id == user_id,
        UserBook.book_id == book_id
    ).first()

    if not user_book:
        raise ValueError("User-book relationship not found")

    # Create the reminder
    scheduled_for = datetime.utcnow() + timedelta(days=days_ahead)
    reminder = Reminder(
        user_book_id=user_book.id,
        reminder_type=reminder_type,
        scheduled_for=scheduled_for
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return reminder

def get_due_reminders(db):
    """
    Retrieves reminders that are due to be sent.
    """
    current_time = datetime.utcnow()
    return db.query(Reminder).filter(
        Reminder.scheduled_for <= current_time,
        Reminder.sent == False
    ).all()

def mark_reminder_sent(db, reminder_id):
    """
    Marks a reminder as sent.
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder:
        reminder.sent = True
        reminder.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
    return reminder

def save_quiz_to_db(db, user_id, book_id, question, correct_answer):
    """
    Saves a quiz question to the database.
    """
    quiz = Quiz(
        user_id=user_id,
        book_id=book_id,
        question=question,
        correct_answer=correct_answer
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz

def save_quiz_answer(db, quiz_id, user_answer, is_correct):
    """
    Saves a user's answer to a quiz question.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        quiz.user_answer = user_answer
        quiz.is_correct = is_correct
        quiz.answered_at = datetime.utcnow()
        db.commit()
        db.refresh(quiz)
    return quiz

def get_user_books(db, user_id):
    """
    Retrieves all books associated with a user.
    """
    return db.query(UserBook).filter(UserBook.user_id == user_id).all()

def get_user_progress(db, user_id, book_id):
    """
    Retrieves a user's progress for a specific book.
    """
    user_book = db.query(UserBook).filter(
        UserBook.user_id == user_id,
        UserBook.book_id == book_id
    ).first()

    if not user_book:
        return None

    # Get quiz statistics
    total_quizzes = db.query(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.book_id == book_id
    ).count()

    correct_quizzes = db.query(Quiz).filter(
        Quiz.user_id == user_id,
        Quiz.book_id == book_id,
        Quiz.is_correct == True
    ).count()

    # Calculate retention score
    retention_score = 0
    if total_quizzes > 0:
        retention_score = (correct_quizzes / total_quizzes) * 100

    # Update the retention score
    user_book.retention_score = retention_score
    db.commit()

    return user_book

def initialize_recommended_books(db):
    """
    Initializes the database with recommended books.
    """
    recommended_books = [
        {
            "title": "Atomic Habits",
            "author": "James Clear",
            "description": "An easy and proven way to build good habits and break bad ones."
        },
        {
            "title": "Sapiens",
            "author": "Yuval Noah Harari",
            "description": "A brief history of humankind."
        },
        {
            "title": "The Psychology of Money",
            "author": "Morgan Housel",
            "description": "Timeless lessons on wealth, greed, and happiness."
        },
        {
            "title": "Thinking, Fast and Slow",
            "author": "Daniel Kahneman",
            "description": "How two systems drive the way we think and make choices."
        },
        {
            "title": "Deep Work",
            "author": "Cal Newport",
            "description": "Rules for focused success in a distracted world."
        }
    ]

    for book_data in recommended_books:
        existing_book = db.query(Book).filter(Book.title == book_data["title"]).first()
        if not existing_book:
            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                description=book_data["description"],
                is_recommended=True
            )
            db.add(book)

    db.commit()