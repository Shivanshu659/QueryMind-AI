"""
Application configuration for QueryMind AI.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT / "database"
LOG_DIR = PROJECT_ROOT / "logs"


# ---------------------------------------------------------
# Environment variables
# ---------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# ---------------------------------------------------------
# Application settings
# ---------------------------------------------------------

APP_NAME = "QueryMind AI"

APP_VERSION = "1.0.0"

MAX_QUESTION_LENGTH = 2000

MAX_SQL_LENGTH = 20000

MAX_HISTORY_ITEMS = 20

MAX_RESULT_ROWS = 10000


# ---------------------------------------------------------
# Database settings
# ---------------------------------------------------------

DATABASE_PATH = DATABASE_DIR / "chinook.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ---------------------------------------------------------
# Sample questions
# ---------------------------------------------------------

SAMPLE_QUESTIONS_PATH = (
    DATA_DIR / "sample_questions.json"
)