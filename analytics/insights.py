"""
Automatic result analysis for QueryMind AI.
"""

import pandas as pd


def analyze_dataframe(
    dataframe: pd.DataFrame,
) -> dict:
    """
    Generate basic insights from a query result.
    """

    if dataframe is None:
        return {
            "rows": 0,
            "columns": 0,
            "numeric_columns": [],
            "categorical_columns": [],
            "missing_values": 0,
            "insights": [],
        }

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = dataframe.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    missing_values = int(
        dataframe.isna().sum().sum()
    )

    insights = []

    if len(dataframe) > 0:
        insights.append(
            f"The query returned {len(dataframe):,} rows "
            f"across {len(dataframe.columns)} columns."
        )

    if numeric_columns:
        insights.append(
            f"Numeric analysis is available for: "
            f"{', '.join(numeric_columns[:5])}."
        )

    if categorical_columns:
        insights.append(
            f"Categorical analysis is available for: "
            f"{', '.join(categorical_columns[:5])}."
        )

    if missing_values:
        insights.append(
            f"The result contains {missing_values:,} missing values."
        )
    else:
        insights.append(
            "No missing values were found in the result."
        )

    return {
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "missing_values": missing_values,
        "insights": insights,
    }


def get_numeric_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return descriptive statistics for numeric columns.
    """

    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    numeric_data = dataframe.select_dtypes(
        include="number"
    )

    if numeric_data.empty:
        return pd.DataFrame()

    return numeric_data.describe().T