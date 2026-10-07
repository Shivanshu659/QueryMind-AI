import pytest

from llm.sql_corrector import correct_sql


def test_empty_question_rejected():
    with pytest.raises(ValueError):
        correct_sql(
            question="",
            failed_sql="SELECT * FROM Artist",
            error_message="some error",
        )


def test_empty_sql_rejected():
    with pytest.raises(ValueError):
        correct_sql(
            question="Show artists",
            failed_sql="",
            error_message="some error",
        )


def test_empty_error_rejected():
    with pytest.raises(ValueError):
        correct_sql(
            question="Show artists",
            failed_sql="SELECT * FROM Artist",
            error_message="",
        )


def test_question_length_limit():
    with pytest.raises(ValueError):
        correct_sql(
            question="A" * 2001,
            failed_sql="SELECT * FROM Artist",
            error_message="some error",
        )