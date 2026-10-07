from pydantic import BaseModel, Field

from llm.client import get_model
from llm.prompts import sql_prompt
from llm.schema_context import build_schema_context


class SQLCorrectionResult(BaseModel):
    sql: str = Field(
        description="The corrected read-only SQL query."
    )

    explanation: str = Field(
        description="A short explanation of what was corrected."
    )

    correction_needed: bool = Field(
        description="Whether the SQL required correction."
    )


def correct_sql(
    question: str,
    failed_sql: str,
    error_message: str,
) -> SQLCorrectionResult:
    """
    Ask the LLM to correct SQL that failed during execution.
    """

    question = question.strip()
    failed_sql = failed_sql.strip()
    error_message = error_message.strip()

    if not question:
        raise ValueError("Original question cannot be empty.")

    if not failed_sql:
        raise ValueError("Failed SQL cannot be empty.")

    if not error_message:
        raise ValueError("Database error cannot be empty.")

    if len(question) > 2000:
        raise ValueError("Question is too long.")

    if len(failed_sql) > 20000:
        raise ValueError("SQL query is too long.")

    if len(error_message) > 5000:
        error_message = error_message[:5000]

    database_schema = build_schema_context()

    correction_prompt = f"""
You are an expert SQLite SQL debugging assistant.

The user asked:

{question}

The generated SQL was:

{failed_sql}

The database returned this error:

{error_message}

Database schema:

{database_schema}

Your task is to correct the SQL query.

Rules:

1. Return only a read-only SELECT query.
2. WITH ... SELECT queries are allowed.
3. Do not use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   ATTACH, PRAGMA, or other database-modifying operations.
4. Use only tables and columns that exist in the supplied schema.
5. Preserve the original user's intended question.
6. Correct the SQL based on the database error.
7. Do not invent tables or columns.
8. Use explicit JOIN conditions.
9. Do not add unnecessary complexity.
10. Do not include Markdown formatting.
11. If the original question cannot be answered using the schema,
    return the safest possible SQL and explain the limitation.

Return:

- corrected SQL
- short explanation
- whether correction was necessary
"""

    model = get_model()

    structured_model = model.with_structured_output(
        SQLCorrectionResult
    )

    result = structured_model.invoke(
        correction_prompt
    )

    return result