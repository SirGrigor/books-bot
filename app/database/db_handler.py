from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Define the base class for declarative models <button class="citation-flag" data-index="5">
Base = declarative_base()

class User(Base):
    """
    Represents a user in the database.
    Each user is identified by their unique chat_id.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)  # Unique identifier for the user (Telegram chat_id)
    book_title = Column(String)  # Title of the book (optional)
    summary = Column(Text)  # Summary associated with the user (optional)

class SummaryModel(Base):
    """
    Represents a summary record in the database.
    Each summary is tied to a specific user via their chat_id.
    """
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # The chat_id of the user who requested the summary
    title = Column(String)  # Chapter title or "Short Text"
    summary = Column(Text)  # Generated summary

def init_db(db_url):
    """
    Initializes the database by creating an engine and tables.
    Returns a sessionmaker instance for creating sessions.
    """
    engine = create_engine(db_url)  # Create the database engine <button class="citation-flag" data-index="10">
    Base.metadata.create_all(engine)  # Create all tables if they don't exist
    return sessionmaker(bind=engine)  # Return a session factory <button class="citation-flag" data-index="4">

class DBHandler:
    """
    Handles database operations such as saving summaries and retrieving user data.
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_summary(self, summary_model):
        """
        Saves a summary record to the database.
        """
        session = self.session_factory()  # Create a new session
        try:
            session.add(summary_model)  # Add the summary model to the session
            session.commit()  # Commit the transaction to save changes
        except Exception as e:
            session.rollback()  # Rollback in case of an error
            raise e
        finally:
            session.close()  # Ensure the session is closed

    def get_user_summaries(self, user_id):
        """
        Retrieves all summaries associated with a specific user.
        """
        session = self.session_factory()  # Create a new session
        try:
            summaries = session.query(SummaryModel).filter_by(user_id=user_id).all()
            return summaries
        finally:
            session.close()  # Ensure the session is closed

    def save_user(self, user):
        """
        Saves a user record to the database.
        """
        session = self.session_factory()  # Create a new session
        try:
            session.add(user)  # Add the user model to the session
            session.commit()  # Commit the transaction to save changes
        except Exception as e:
            session.rollback()  # Rollback in case of an error
            raise e
        finally:
            session.close()  # Ensure the session is closed

    def get_user_by_chat_id(self, chat_id):
        """
        Retrieves a user by their chat_id.
        """
        session = self.session_factory()  # Create a new session
        try:
            user = session.query(User).filter_by(chat_id=chat_id).first()
            return user
        finally:
            session.close()  # Ensure the session is closed