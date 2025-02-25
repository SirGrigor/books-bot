# app/database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# User model - already exists, but adding relationships
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

# Message model - already exists, adding relationship
class Message(Base):
	__tablename__ = "messages"
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
	message_text = Column(Text, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)

	# Relationships
	user = relationship("User", back_populates="messages")

# Summary model - already exists, adding relationships
class Summary(Base):
	__tablename__ = "summaries"
	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
	title = Column(String)
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