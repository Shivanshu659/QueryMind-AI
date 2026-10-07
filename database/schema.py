import json

from sqlalchemy import inspect

from database.connection import get_engine


def get_database_schema() -> dict:
    """
    Extract table names, columns, primary keys,
    foreign keys, and indexes from the database.
    """
    engine = get_engine()
    inspector = inspect(engine)

    schema = {}

    for table_name in inspector.get_table_names():
        columns = []

        for column in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "primary_key": column.get("primary_key", False),
                    "default": (
                        str(column["default"])
                        if column.get("default") is not None
                        else None
                    ),
                }
            )

        foreign_keys = []

        for foreign_key in inspector.get_foreign_keys(table_name):
            foreign_keys.append(
                {
                    "columns": foreign_key["constrained_columns"],
                    "referenced_table": foreign_key["referred_table"],
                    "referenced_columns": foreign_key[
                        "referred_columns"
                    ],
                }
            )

        indexes = []

        for index in inspector.get_indexes(table_name):
            indexes.append(
                {
                    "name": index["name"],
                    "columns": index["column_names"],
                    "unique": index["unique"],
                }
            )

        schema[table_name] = {
            "columns": columns,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
        }

    return schema


def get_table_names() -> list[str]:
    """Return all table names in the database."""
    engine = get_engine()

    return inspect(engine).get_table_names()


def get_table_details(table_name: str) -> dict:
    """Return schema information for a specific table."""
    schema = get_database_schema()

    if table_name not in schema:
        raise ValueError(f"Unknown table: {table_name}")

    return schema[table_name]


def search_schema(search_term: str) -> list[dict]:
    """
    Search table names and column names without
    querying or modifying the table data.
    """
    schema = get_database_schema()
    search_term = search_term.strip().casefold()

    if not search_term:
        return []

    matches = []

    for table_name, details in schema.items():
        if search_term in table_name.casefold():
            matches.append(
                {
                    "table": table_name,
                    "column": None,
                    "type": None,
                    "match_type": "table",
                }
            )

        for column in details["columns"]:
            if search_term in column["name"].casefold():
                matches.append(
                    {
                        "table": table_name,
                        "column": column["name"],
                        "type": column["type"],
                        "match_type": "column",
                    }
                )

    return matches


def export_schema_json() -> str:
    """Return schema metadata as formatted JSON."""
    schema = get_database_schema()

    return json.dumps(
        schema,
        indent=2,
        ensure_ascii=False,
    )


def print_database_schema() -> None:
    """Print a readable database schema summary."""
    schema = get_database_schema()

    print("\nDATABASE SCHEMA")
    print("=" * 70)

    for table_name, details in schema.items():
        print(f"\nTABLE: {table_name}")

        for column in details["columns"]:
            flags = []

            if column["primary_key"]:
                flags.append("PRIMARY KEY")

            if not column["nullable"]:
                flags.append("NOT NULL")

            flag_text = f" [{', '.join(flags)}]" if flags else ""

            print(
                f"  {column['name']} "
                f"({column['type']}){flag_text}"
            )

        for foreign_key in details["foreign_keys"]:
            print(
                "  FOREIGN KEY: "
                f"{foreign_key['columns']} -> "
                f"{foreign_key['referenced_table']}."
                f"{foreign_key['referenced_columns']}"
            )


if __name__ == "__main__":
    print_database_schema()