# app/database/db_handler.py - COMPLETE FIXED VERSION

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, desc, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from constants.constants import DATABASE_URL
import logging

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, unique=True, index=True)  # Telegram user ID
    username = Column(String)  # Telegram username
    first_name = Column(String)  # First name of the user
    created_at = Column(DateTime, default=datetime.utcnow)  # Added created_at field
    learning_style = Column(String, nullable=True)  # User's preferred learning style (visual, auditory, etc.)
    interests = Column(Text, nullable=True)  # User's stated interests for content personalization

# Define the Message model
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Telegram user ID
    message_text = Column(Text, nullable=False)  # Content of the message
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

# Define the Summary model
class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # Telegram user ID
    title = Column(String, nullable=True)  # Optional title (e.g., chapter name)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    book_id = Column(Integer, nullable=True)  # Foreign key to books.id
    created_at = Column(DateTime, default=datetime.utcnow)
    chapter_number = Column(Integer, nullable=True)  # Chapter number if part of a book
    key_concepts = Column(Text, nullable=True)  # Key concepts as JSON string

# New model for books
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_recommended = Column(Boolean, default=False)  # Whether this is a curated book
    created_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String, nullable=True)  # Book category or genre
    tags = Column(String, nullable=True)  # Comma-separated tags

# New model for user-book relationships
class UserBook(Base):
    __tablename__ = "user_books"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    book_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    retention_score = Column(Float, default=0.0)  # 0-100% retention score
    last_interaction = Column(DateTime, nullable=True)  # Last time user interacted with this book

# New model for spaced repetition reminders
class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_book_id = Column(Integer, nullable=False)
    reminder_type = Column(String, nullable=False)  # 'summary', 'quiz', 'teaching'
    scheduled_for = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    stage = Column(Integer, default=1)  # Spaced repetition stage (1-4)
    response_received = Column(Boolean, default=False)  # Whether user responded

# New model for quizzes
class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    book_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    summary_id = Column(Integer, nullable=True)  # Related summary ID if applicable
    difficulty = Column(Integer, nullable=True)  # Question difficulty (1-5)

# New model for chapters
class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    chapter_number = Column(Integer, nullable=True)
    content_start_pos = Column(Integer, nullable=True)  # Start position in the book text
    content_end_pos = Column(Integer, nullable=True)    # End position in the book text
    created_at = Column(DateTime, default=datetime.utcnow)

# New model for teaching exercises
class TeachingExercise(Base):
    __tablename__ = "teaching_exercises"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    book_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    user_response = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

# Create tables - force create all tables at startup
def create_tables():
    """
    Create all tables if they don't exist
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")

# Function to save user metadata
def save_user_to_db(db, user_id, username, first_name):
    """
    Saves a user to the database or updates an existing user.
    """
    try:
        db_user = db.query(User).filter(User.user_id == str(user_id)).first()
        if not db_user:
            db_user = User(
                user_id=str(user_id),
                username=username,
                first_name=first_name
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving user: {str(e)}")
        raise

# Function to save a message
def save_message_to_db(db, user_id, message_text):
    """
    Saves a message to the database.
    """
    try:
        db_message = Message(user_id=str(user_id), message_text=message_text)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving message: {str(e)}")
        raise

# Function to save a summary
def save_summary_to_db(db, user_id, title, original_text, summary, book_id=None, chapter_number=None):
    """
    Saves a summary to the database.
    """
    try:
        db_summary = Summary(
            user_id=str(user_id),
            title=title,
            original_text=original_text,
            summary=summary,
            book_id=book_id,
            chapter_number=chapter_number
        )
        db.add(db_summary)
        db.commit()
        db.refresh(db_summary)
        return db_summary
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving summary: {str(e)}")
        raise

# Functions for book management
def get_recommended_books(db):
    """
    Retrieves the list of curated recommended books.
    """
    try:
        return db.query(Book).filter(Book.is_recommended == True).all()
    except Exception as e:
        logging.error(f"Error getting recommended books: {str(e)}")
        return []

def add_custom_book_to_db(db, title, user_id, author=None, description=None):
    """
    Adds a custom book to the database.
    """
    try:
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

        # Check if user already has this book
        existing_user_book = db.query(UserBook).filter(
            UserBook.user_id == str(user_id),
            UserBook.book_id == book.id
        ).first()

        if not existing_user_book:
            # Create user-book relationship
            user_book = UserBook(
                user_id=str(user_id),
                book_id=book.id,
                started_at=datetime.utcnow()
            )
            db.add(user_book)
            db.commit()
            db.refresh(user_book)

        return book
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding custom book: {str(e)}")
        raise

def save_book_selection_to_db(db, user_id, book_id):
    """
    Saves a user's book selection.
    """
    try:
        # Get the book
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError("Book not found")

        # Check if user already has this book
        existing_user_book = db.query(UserBook).filter(
            UserBook.user_id == str(user_id),
            UserBook.book_id == book_id
        ).first()

        if existing_user_book:
            user_book = existing_user_book
            # Update last interaction time
            user_book.last_interaction = datetime.utcnow()
            db.commit()
        else:
            user_book = UserBook(
                user_id=str(user_id),
                book_id=book_id,
                started_at=datetime.utcnow(),
                last_interaction=datetime.utcnow()
            )
            db.add(user_book)
            db.commit()
            db.refresh(user_book)

        return book
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving book selection: {str(e)}")
        raise

def create_reminder(db, user_id, book_id, reminder_type, days_ahead, stage=1):
    """
    Creates a spaced repetition reminder.
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
            stage=stage
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        return reminder
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating reminder: {str(e)}")
        raise

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
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.sent = True
            reminder.sent_at = datetime.utcnow()
            db.commit()
            db.refresh(reminder)
        return reminder
    except Exception as e:
        db.rollback()
        logging.error(f"Error marking reminder as sent: {str(e)}")
        raise

def save_quiz_to_db(db, user_id, book_id, question, correct_answer, difficulty=None, summary_id=None):
    """
    Saves a quiz question to the database.
    """
    try:
        quiz = Quiz(
            user_id=str(user_id),
            book_id=book_id,
            question=question,
            correct_answer=correct_answer,
            difficulty=difficulty,
            summary_id=summary_id
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving quiz: {str(e)}")
        raise

def save_quiz_answer(db, quiz_id, user_answer, is_correct):
    """
    Saves a user's answer to a quiz question.
    """
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz:
            quiz.user_answer = user_answer
            quiz.is_correct = is_correct
            quiz.answered_at = datetime.utcnow()
            db.commit()
            db.refresh(quiz)
        return quiz
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving quiz answer: {str(e)}")
        raise

def get_user_books(db, user_id):
    """
    Retrieves all books associated with a user.
    """
    try:
        user_books = db.query(UserBook).filter(UserBook.user_id == str(user_id)).all()
        return user_books
    except Exception as e:
        logging.error(f"Error getting user books: {str(e)}")
        return []

def get_user_progress(db, user_id, book_id):
    """
    Retrieves a user's progress for a specific book.
    """
    try:
        user_book = db.query(UserBook).filter(
            UserBook.user_id == str(user_id),
            UserBook.book_id == book_id
        ).first()

        if not user_book:
            return None

        # Get quiz statistics
        total_quizzes = db.query(Quiz).filter(
            Quiz.user_id == str(user_id),
            Quiz.book_id == book_id
        ).count()

        correct_quizzes = db.query(Quiz).filter(
            Quiz.user_id == str(user_id),
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
    except Exception as e:
        db.rollback()
        logging.error(f"Error getting user progress: {str(e)}")
        return None

def initialize_recommended_books(db):
    """
    Initializes the database with recommended books.
    """
    try:
        # Check if we already have recommended books
        existing_count = db.query(Book).filter(Book.is_recommended == True).count()
        if existing_count > 0:
            logging.info(f"Found {existing_count} existing recommended books, skipping initialization")
            return

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
        logging.info(f"Added recommended books to database")
    except Exception as e:
        db.rollback()
        logging.error(f"Error initializing recommended books: {str(e)}")

# New NLP-related functions

def save_chapter_to_db(db, book_id, title, chapter_number, start_pos, end_pos):
    """
    Saves a detected chapter to the database.
    """
    try:
        chapter = Chapter(
            book_id=book_id,
            title=title,
            chapter_number=chapter_number,
            content_start_pos=start_pos,
            content_end_pos=end_pos
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving chapter: {str(e)}")
        raise

def save_teaching_exercise_to_db(db, user_id, book_id, prompt):
    """
    Saves a teaching exercise to the database.
    """
    try:
        exercise = TeachingExercise(
            user_id=str(user_id),
            book_id=book_id,
            prompt=prompt
        )
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        return exercise
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving teaching exercise: {str(e)}")
        raise

def save_teaching_response_to_db(db, exercise_id, user_response, feedback=None):
    """
    Saves a user's response to a teaching exercise.
    """
    try:
        exercise = db.query(TeachingExercise).filter(TeachingExercise.id == exercise_id).first()
        if exercise:
            exercise.user_response = user_response
            exercise.feedback = feedback
            exercise.responded_at = datetime.utcnow()
            db.commit()
            db.refresh(exercise)
        return exercise
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving teaching response: {str(e)}")
        raise

def update_user_preferences(db, user_id, learning_style=None, interests=None):
    """
    Updates user preferences for learning style and interests.
    """
    try:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        if user:
            if learning_style:
                user.learning_style = learning_style
            if interests:
                user.interests = interests
            db.commit()
            db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating user preferences: {str(e)}")
        raise

def update_reminder_response(db, reminder_id, response_received=True):
    """
    Updates a reminder to note that the user has responded.
    """
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.response_received = response_received
            db.commit()
            db.refresh(reminder)
        return reminder
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating reminder response: {str(e)}")
        raise

def get_book_chapters(db, book_id):
    """
    Retrieves all chapters for a book.
    """
    try:
        chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
        return chapters
    except Exception as e:
        logging.error(f"Error getting book chapters: {str(e)}")
        return []

def get_user_learning_data(db, user_id, book_id=None):
    """
    Retrieves comprehensive learning data for a user, optionally filtered by book.
    """
    try:
        result = {
            "quiz_stats": {
                "total": 0,
                "correct": 0,
                "incorrect": 0,
                "not_answered": 0
            },
            "teaching_stats": {
                "total": 0,
                "responded": 0,
                "not_responded": 0
            },
            "reminder_stats": {
                "total": 0,
                "responded_to": 0,
                "not_responded": 0
            },
            "retention_score": 0
        }

        # Base query filters
        quiz_filter = [Quiz.user_id == str(user_id)]
        teaching_filter = [TeachingExercise.user_id == str(user_id)]
        reminder_filter = []

        # Add book filter if specified
        if book_id:
            quiz_filter.append(Quiz.book_id == book_id)
            teaching_filter.append(TeachingExercise.book_id == book_id)

            # For reminders, we need to get the user_book_id first
            user_book = db.query(UserBook).filter(
                UserBook.user_id == str(user_id),
                UserBook.book_id == book_id
            ).first()

            if user_book:
                reminder_filter.append(Reminder.user_book_id == user_book.id)

        # Calculate quiz stats
        quizzes = db.query(Quiz).filter(*quiz_filter).all()
        result["quiz_stats"]["total"] = len(quizzes)
        result["quiz_stats"]["correct"] = sum(1 for q in quizzes if q.is_correct is True)
        result["quiz_stats"]["incorrect"] = sum(1 for q in quizzes if q.is_correct is False)
        result["quiz_stats"]["not_answered"] = sum(1 for q in quizzes if q.user_answer is None)

        # Calculate teaching stats
        exercises = db.query(TeachingExercise).filter(*teaching_filter).all()
        result["teaching_stats"]["total"] = len(exercises)
        result["teaching_stats"]["responded"] = sum(1 for e in exercises if e.user_response is not None)
        result["teaching_stats"]["not_responded"] = sum(1 for e in exercises if e.user_response is None)

        # Calculate reminder stats
        if reminder_filter:
            reminders = db.query(Reminder).filter(*reminder_filter).all()
            result["reminder_stats"]["total"] = len(reminders)
            result["reminder_stats"]["responded_to"] = sum(1 for r in reminders if r.response_received)
            result["reminder_stats"]["not_responded"] = sum(1 for r in reminders if not r.response_received)

        # Calculate overall retention score
        if book_id:
            user_book = db.query(UserBook).filter(
                UserBook.user_id == str(user_id),
                UserBook.book_id == book_id
            ).first()

            if user_book:
                result["retention_score"] = user_book.retention_score
        else:
            # Average retention across all books
            user_books = db.query(UserBook).filter(UserBook.user_id == str(user_id)).all()
            if user_books:
                result["retention_score"] = sum(ub.retention_score for ub in user_books) / len(user_books)

        return result
    except Exception as e:
        logging.error(f"Error getting user learning data: {str(e)}")
        return result

# Create the tables when the module is imported
create_tables()