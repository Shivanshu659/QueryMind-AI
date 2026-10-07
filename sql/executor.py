import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_engine
from sql.validator import validate_sql, SQLValidationError


MAX_ROWS = 1000


class SQLExecutionError(RuntimeError):
    """Raised when a SQL query cannot be executed safely."""


def execute_sql(sql: str, max_rows: int = MAX_ROWS) -> pd.DataFrame:
    """
    Validate and execute a read-only query.

    Returns at most max_rows rows.
    """
    if not isinstance(max_rows, int) or isinstance(max_rows, bool):
        raise ValueError("max_rows must be an integer.")

    if not 1 <= max_rows <= MAX_ROWS:
        raise ValueError(f"max_rows must be between 1 and {MAX_ROWS}.")

    validated_sql = validate_sql(sql)

    # Use the database's read-only URI mode as a second protection layer.
    # This assumes the project's database path is database/chinook.db.
    from pathlib import Path
    from sqlalchemy import create_engine

    database_path = (
        Path(__file__).resolve().parent.parent
        / "database"
        / "chinook.db"
    ).resolve()

    if not database_path.is_file():
        raise SQLExecutionError(
            f"Database file not found: {database_path}"
        )

    read_only_engine = create_engine(
        f"sqlite:///file:{database_path.as_posix()}?mode=ro&uri=true",
        connect_args={"timeout": 5},
    )

    try:
        with read_only_engine.connect() as connection:
            # A LIMIT bounds returned rows, not necessarily query cost.
            # Fetch one extra row to detect truncation.
            limited_sql = (
                f"SELECT * FROM ({validated_sql}) "
                f"AS querymind_result LIMIT {max_rows + 1}"
            )

            result = connection.execute(text(limited_sql))
            rows = result.fetchmany(max_rows + 1)
            columns = list(result.keys())

            truncated = len(rows) > max_rows
            rows = rows[:max_rows]

            dataframe = pd.DataFrame(rows, columns=columns)
            dataframe.attrs["truncated"] = truncated
            dataframe.attrs["max_rows"] = max_rows

            return dataframe

    except SQLValidationError:
        raise
    except SQLAlchemyError as exc:
        raise SQLExecutionError(
            f"Database could not execute this query: {exc}"
        ) from exc
    finally:
        read_only_engine.dispose()