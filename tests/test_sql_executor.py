from sql.executor import execute_sql


def test_executor_returns_dataframe():
    result = execute_sql("SELECT Name FROM Artist LIMIT 5")

    assert list(result.columns) == ["Name"]
    assert len(result) <= 5


def test_executor_marks_truncated_results():
    result = execute_sql("SELECT Name FROM Artist", max_rows=2)

    assert len(result) <= 2
    assert result.attrs["truncated"] is True