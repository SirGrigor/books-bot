Book Retention Bot
A Telegram bot that helps users retain knowledge from books using AI-powered summaries and scientifically optimized spaced repetition.
Overview
Most people forget 90% of what they read within weeks. This bot leverages spaced repetition, active recall, and AI technology to help you remember key insights from books without changing your routine.
Features
Core Functionality

Book Selection: Choose from a curated list of popular nonfiction books or add your own
AI Summaries: Get concise summaries of key book insights
Spaced Repetition: Receive reminders at scientifically optimized intervals (1, 3, 7, 30 days)
Interactive Learning: Engage with quiz questions and teaching challenges
Progress Tracking: Monitor your retention and learning journey

User Experience

Simple Interface: Easy-to-use commands via Telegram
No Setup Required: Works in your existing Telegram chat
Effortless Learning: Requires minimal time investment (a few minutes per day)

Technical Details
Architecture

Python-based Telegram bot using python-telegram-bot library
SQLite database for user data and spaced repetition scheduling
Google's Gemini API for AI-powered summarization and question generation
APScheduler for managing timed reminders

Components

Controllers: Handle user interactions and commands
Services: Provide core functionality (summarization, quizzes, teaching)
Database Models: Store user data, books, and learning progress
Utilities: Helper functions for file processing and text chunking

Setup and Installation

Clone the repository
Copygit clone <repository-url>
cd book-retention-bot

Set up environment variables
Create a .env file with the following variables:
CopyTELEGRAM_BOT_TOKEN=your_telegram_bot_token
GENAI_API_KEY=your_google_ai_api_key
DATABASE_URL=sqlite:///bot.db
LOG_LEVEL=INFO

Install dependencies
Copypoetry install
or
Copypip install -r requirements.txt

Run database migrations
Copypython migrations.py

Start the bot
Copypython main.py


Usage
Basic Commands

/start - Welcome message and introduction
/help - Display available commands

Book Selection

/selectbook - Choose from curated list of books
/addbook - Add a custom book by title

Learning Features

/summary - Get or view a book summary
/quiz - Test your knowledge with quiz questions
/teach - Practice explaining concepts in your own words
/progress - View your reading and retention statistics

Project Structure
Copybook-retention-bot/
├── app/
│   ├── controllers/           # Command handlers
│   ├── database/              # Database models and connections
│   ├── models/                # Data models
│   ├── services/              # Business logic
│   └── utils/                 # Helper functions
├── constants/                 # Configuration constants
├── downloads/                 # Temporary storage for uploaded files
├── main.py                    # Application entry point
├── migrations.py              # Database migration script
├── pyproject.toml             # Project metadata and dependencies
└── .env                       # Environment variables
Future Enhancements
Phase 1 (Current)

Basic text-based summaries and interactions
Fundamental spaced repetition system
Simple quiz and teaching components

Phase 2 (Planned)

AI-generated audio summaries (podcast-style)
Infographic visual summaries
More advanced discussion capabilities
Enhanced teaching feedback
Social learning features

License
[Insert License Information]
Acknowledgements

Spaced repetition research and methodology
Python Telegram Bot library
Google Gemini AI
Contributors and testers