from pydantic import BaseModel, Field

from llm.client import get_model
from llm.prompts import sql_prompt
from llm.schema_context import build_schema_context


class SQLGenerationResult(BaseModel):
    sql: str = Field(
        description="One SQLite SELECT query, or empty if unclear."
    )

    explanation: str = Field(
        description="A concise explanation of the intended query."
    )

    tables_used: list[str] = Field(
        description="Tables referenced by the generated query."
    )

    clarification_needed: bool = Field(
        description="Whether the user must clarify the question."
    )

    clarification_question: str = Field(
        description="Clarification question, or an empty string."
    )


def generate_sql(question: str) -> SQLGenerationResult:
    """
    Generate SQL from a natural-language business question.
    Does not execute the generated SQL.
    """
    question = question.strip()

    if not question:
        raise ValueError(
            "Please enter a business question."
        )

    if len(question) > 2000:
        raise ValueError(
            "The question must be 2000 characters or fewer."
        )

    database_schema = build_schema_context()
    model = get_model()

    structured_model = model.with_structured_output(
        SQLGenerationResult
    )

    chain = sql_prompt | structured_model

    result = chain.invoke(
        {
            "database_schema": database_schema,
            "question": question,
        }
    )

    return result