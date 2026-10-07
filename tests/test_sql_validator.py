import pytest

from sql.validator import (
    SQLValidationError,
    validate_sql,
)


def test_accepts_simple_select():
    sql = validate_sql("SELECT Name FROM Artist LIMIT 10")
    assert "SELECT" in sql.upper()
    assert "ARTIST" in sql.upper()


def test_accepts_with_select():
    sql = """
    WITH top_artists AS (
        SELECT Name FROM Artist LIMIT 5
    )
    SELECT Name FROM top_artists
    """
    assert "WITH" in validate_sql(sql).upper()


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "DELETE FROM Artist",
        "UPDATE Artist SET Name = 'Changed'",
        "DROP TABLE Artist",
        "SELECT * FROM Artist; DELETE FROM Artist",
        "SELECT * FROM sqlite_master",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_rejects_invalid_syntax():
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT FROM Artist")