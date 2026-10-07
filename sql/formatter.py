"""
SQL formatting utilities for QueryMind AI.
"""

import sqlglot
from sqlglot import expressions as exp


def format_sql(sql: str) -> str:
    """
    Format SQL into a readable, consistently structured form.

    Parameters
    ----------
    sql : str
        SQL query to format.

    Returns
    -------
    str
        Formatted SQL query.

    Raises
    ------
    ValueError
        If the SQL query is empty or cannot be parsed.
    """

    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    sql = sql.strip()

    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")

        return parsed.sql(
            dialect="sqlite",
            pretty=True,
        )

    except Exception as exc:
        raise ValueError(
            f"Unable to format SQL query: {exc}"
        ) from exc


def normalize_sql(sql: str) -> str:
    """
    Normalize SQL into a compact single-line representation.

    Useful for logging, comparison, and query history.
    """

    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    try:
        parsed = sqlglot.parse_one(
            sql.strip(),
            read="sqlite",
        )

        return parsed.sql(
            dialect="sqlite",
            pretty=False,
        )

    except Exception as exc:
        raise ValueError(
            f"Unable to normalize SQL query: {exc}"
        ) from exc


def is_select_query(sql: str) -> bool:
    """
    Check whether the supplied SQL represents a SELECT query.

    WITH queries are also accepted when their final statement
    is a SELECT.
    """

    if not sql or not sql.strip():
        return False

    try:
        parsed = sqlglot.parse_one(
            sql.strip(),
            read="sqlite",
        )

        return isinstance(parsed, exp.Select) or (
            isinstance(parsed, exp.With)
            and parsed.find(exp.Select) is not None
        )

    except Exception:
        return False