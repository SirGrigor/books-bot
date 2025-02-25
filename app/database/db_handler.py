# app/database/db_handler.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, desc
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    books = relationship("UserBook", back_populates="user")
    messages = relationship("Message", back_populates="user")
    summaries = relationship("Summary", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")

# Define the Message model
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    message_text = Column(Text, nullable=False)  # Content of the message
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

    # Relationships
    user = relationship("User", back_populates="messages")

# Define the Summary model
class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String)  # Optional title (e.g., chapter name)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="summaries")
    book_id = Column(Integer, ForeignKey("books.id"), nullable=True)
    book = relationship("Book", back_populates="summaries")

# New model for books
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_recommended = Column(Boolean, default=False)  # Whether this is a curated book
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_books = relationship("UserBook", back_populates="book")
    summaries = relationship("Summary", back_populates="book")
    quizzes = relationship("Quiz", back_populates="book")

# New model for user-book relationships
class UserBook(Base):
    __tablename__ = "user_books"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    retention_score = Column(Float, default=0.0)  # 0-100% retention score

    # Relationships
    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="user_books")
    reminders = relationship("Reminder", back_populates="user_book")

# New model for spaced repetition reminders
class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_book_id = Column(Integer, ForeignKey("user_books.id"), nullable=False)
    reminder_type = Column(String, nullable=False)  # 'summary', 'quiz', 'teaching'
    scheduled_for = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    user_book = relationship("UserBook", back_populates="reminders")

# New model for quizzes
class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    question = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="quizzes")
    book = relationship("Book", back_populates="quizzes")

# Create tables - we'll handle this carefully to not disturb existing tables
def create_tables():
    # Safely create tables without dropping existing ones
    try:
        # First check if tables exist
        if not engine.dialect.has_table(engine, "books"):
            Book.__table__.create(engine)
            logging.info("Created books table")

        if not engine.dialect.has_table(engine, "user_books"):
            UserBook.__table__.create(engine)
            logging.info("Created user_books table")

        if not engine.dialect.has_table(engine, "reminders"):
            Reminder.__table__.create(engine)
            logging.info("Created reminders table")

        if not engine.dialect.has_table(engine, "quizzes"):
            Quiz.__table__.create(engine)
            logging.info("Created quizzes table")

        # Add book_id column to Summary if it doesn't exist
        # This requires SQLite specific handling and might need manual migration
        # for now we'll assume the structure from the provided model

        logging.info("Database tables checked/created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")

# Function to save user metadata
def save_user_to_db(db, user_id, username, first_name):
    try:
        db_user = db.query(User).filter(User.user_id == str(user_id)).first()
        if not db_user:
            db_user = User(
                user_id=str(user_id),
                username=username,
                first_name=first_name,
                created_at=datetime.utcnow()
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving user: {str(e)}")
        # Try without created_at as fallback
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
        except Exception as e2:
            db.rollback()
            logging.error(f"Second error saving user: {str(e2)}")
            raise

# Function to save a message
def save_message_to_db(db, user_id, message_text):
    db_message = Message(user_id=str(user_id), message_text=message_text)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Function to save a summary
def save_summary_to_db(db, user_id, title, original_text, summary, book_id=None):
    db_summary = Summary(
        user_id=str(user_id),
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
        UserBook.user_id == str(user_id),
        UserBook.book_id == book_id
    ).first()

    if existing_user_book:
        user_book = existing_user_book
    else:
        user_book = UserBook(
            user_id=str(user_id),
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
        user_id=str(user_id),
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
    user_books = db.query(UserBook).filter(UserBook.user_id == str(user_id)).all()
    return user_books

def get_user_progress(db, user_id, book_id):
    """
    Retrieves a user's progress for a specific book.
    """
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

def initialize_recommended_books(db):
    """
    Initializes the database with recommended books.
    """
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
    logging.info(f"Added {len(recommended_books)} recommended books")

# Create the tables
try:
    create_tables()
except Exception as e:
    logging.error(f"Error during table creation: {str(e)}")