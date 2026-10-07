"""
Automatic visualization utilities for QueryMind AI.
"""

import pandas as pd
import plotly.express as px


def get_chart_columns(
    dataframe: pd.DataFrame,
) -> tuple[str | None, str | None]:
    """
    Identify a categorical column and a numeric column
    suitable for a basic chart.
    """

    if dataframe is None or dataframe.empty:
        return None, None

    categorical_columns = dataframe.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns.tolist()

    category_column = (
        categorical_columns[0]
        if categorical_columns
        else None
    )

    numeric_column = (
        numeric_columns[0]
        if numeric_columns
        else None
    )

    return category_column, numeric_column


def create_bar_chart(
    dataframe: pd.DataFrame,
):
    """
    Create a basic bar chart from the first categorical
    and numeric columns.
    """

    category_column, numeric_column = get_chart_columns(
        dataframe
    )

    if not category_column or not numeric_column:
        return None

    return px.bar(
        dataframe,
        x=category_column,
        y=numeric_column,
        title=f"{numeric_column} by {category_column}",
    )


def create_line_chart(
    dataframe: pd.DataFrame,
):
    """
    Create a line chart when the result contains
    at least two numeric columns.
    """

    if dataframe is None or dataframe.empty:
        return None

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns.tolist()

    if len(numeric_columns) < 2:
        return None

    return px.line(
        dataframe,
        x=numeric_columns[0],
        y=numeric_columns[1],
        title=f"{numeric_columns[1]} by {numeric_columns[0]}",
    )