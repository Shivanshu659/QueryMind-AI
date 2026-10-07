import pytest

from database.schema import (
    get_database_schema,
    get_table_names,
    get_table_details,
    search_schema,
)

from database.explorer import (
    get_table_preview,
)


def test_database_contains_expected_tables():
    tables = get_table_names()

    assert "Customer" in tables
    assert "Invoice" in tables
    assert "Track" in tables


def test_customer_schema_has_customer_id():
    details = get_table_details("Customer")

    column_names = [
        column["name"]
        for column in details["columns"]
    ]

    assert "CustomerId" in column_names


def test_schema_contains_foreign_key_metadata():
    schema = get_database_schema()

    assert "Invoice" in schema
    assert "foreign_keys" in schema["Invoice"]


def test_schema_search_finds_track_id():
    results = search_schema("TrackId")

    assert len(results) > 0

    assert any(
        result["column"] == "TrackId"
        for result in results
    )


def test_table_preview_returns_limited_rows():
    df = get_table_preview("Customer", limit=5)

    assert len(df) <= 5
    assert "CustomerId" in df.columns


def test_unknown_table_is_rejected():
    with pytest.raises(ValueError):
        get_table_details("UnknownTable")


def test_preview_rejects_invalid_limit():
    with pytest.raises(ValueError):
        get_table_preview("Customer", limit=0)