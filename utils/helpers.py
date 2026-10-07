"""
General helper utilities for QueryMind AI.
"""

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_project_root() -> Path:
    """
    Return the root directory of the QueryMind AI project.
    """

    return PROJECT_ROOT


def get_data_path(filename: str) -> Path:
    """
    Return the path to a file inside the data directory.
    """

    if not filename:
        raise ValueError("Filename cannot be empty.")

    return PROJECT_ROOT / "data" / filename


def clean_question(question: str) -> str:
    """
    Clean and normalize a natural-language question.
    """

    if not question:
        return ""

    return " ".join(question.strip().split())


def truncate_text(
    text: str,
    max_length: int = 500,
) -> str:
    """
    Truncate long text while keeping it readable.
    """

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Safely convert a value to an integer.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        return default