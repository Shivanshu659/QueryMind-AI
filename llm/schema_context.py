from database.schema import get_database_schema


def build_schema_context() -> str:
    """
    Format database tables, columns, and foreign keys
    into a readable context for the LLM.
    """
    schema = get_database_schema()

    sections = []

    for table_name, details in schema.items():
        lines = [f"TABLE: {table_name}"]

        for column in details["columns"]:
            attributes = []

            if column["primary_key"]:
                attributes.append("PRIMARY KEY")

            if not column["nullable"]:
                attributes.append("NOT NULL")

            suffix = (
                f" [{', '.join(attributes)}]"
                if attributes
                else ""
            )

            lines.append(
                f"  - {column['name']}: "
                f"{column['type']}{suffix}"
            )

        for foreign_key in details["foreign_keys"]:
            source_columns = ", ".join(
                foreign_key["columns"]
            )

            target_columns = ", ".join(
                foreign_key["referenced_columns"]
            )

            lines.append(
                f"  - FOREIGN KEY ({source_columns}) "
                f"REFERENCES "
                f"{foreign_key['referenced_table']}"
                f"({target_columns})"
            )

        sections.append("\n".join(lines))

    return "\n\n".join(sections)