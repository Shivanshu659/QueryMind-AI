import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    """Raised when SQL does not satisfy the safety rules."""


FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
)


def validate_sql(sql: str) -> str:
    """Validate a single read-only SQLite query."""

    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("SQL query cannot be empty.")

    if len(sql) > 20_000:
        raise SQLValidationError("SQL query is too long.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except Exception as exc:
        raise SQLValidationError(
            f"SQL syntax could not be parsed: {exc}"
        ) from exc

    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError(
            "Only one SQL statement is allowed."
        )

    tree = statements[0]

    if not isinstance(tree, exp.Query):
        raise SQLValidationError(
            "Only read-only SELECT queries are allowed."
        )

    # Ensure the query contains an actual SELECT expression.
    for select_node in tree.find_all(exp.Select):
        if not select_node.expressions:
            raise SQLValidationError(
                "SELECT must specify at least one column or expression."
            )

    for node in tree.walk():
        if isinstance(node, FORBIDDEN_EXPRESSIONS):
            raise SQLValidationError(
                "The query contains a prohibited SQL operation."
            )

        if isinstance(node, exp.Table):
            if node.name.lower().startswith("sqlite_"):
                raise SQLValidationError(
                    "SQLite internal tables cannot be queried."
                )

    return tree.sql(dialect="sqlite")