import pandas as pd

from sqlalchemy import inspect, text

from database.connection import get_engine
from database.schema import get_database_schema


def get_database_summary() -> dict:
    """
    Return basic statistics about the database structure.
    """
    engine = get_engine()
    inspector = inspect(engine)

    table_names = inspector.get_table_names()
    schema = get_database_schema()

    total_columns = sum(
        len(details["columns"])
        for details in schema.values()
    )

    total_foreign_keys = sum(
        len(details["foreign_keys"])
        for details in schema.values()
    )

    return {
        "table_count": len(table_names),
        "column_count": total_columns,
        "foreign_key_count": total_foreign_keys,
        "table_names": table_names,
    }


def get_table_preview(
    table_name: str,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Return a limited preview of a known database table.
    """
    engine = get_engine()
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        raise ValueError(f"Unknown table: {table_name}")

    if not 1 <= limit <= 100:
        raise ValueError("Preview limit must be between 1 and 100.")

    quoted_table = (
        engine.dialect.identifier_preparer.quote(table_name)
    )

    query = text(
        f"SELECT * FROM {quoted_table} LIMIT :row_limit"
    )

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={"row_limit": limit},
        )


def get_table_row_count(table_name: str) -> int:
    """
    Count the rows in a known database table.
    """
    engine = get_engine()
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        raise ValueError(f"Unknown table: {table_name}")

    quoted_table = (
        engine.dialect.identifier_preparer.quote(table_name)
    )

    query = text(
        f"SELECT COUNT(*) FROM {quoted_table}"
    )

    with engine.connect() as connection:
        result = connection.execute(query)

        return result.scalar_one()