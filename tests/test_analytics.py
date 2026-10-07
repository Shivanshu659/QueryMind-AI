import pandas as pd

from analytics.insights import analyze_dataframe
from analytics.visualizer import get_chart_columns


def test_analyze_dataframe():
    dataframe = pd.DataFrame(
        {
            "Country": ["India", "USA", "UK"],
            "Revenue": [100, 200, 150],
        }
    )

    result = analyze_dataframe(dataframe)

    assert result["rows"] == 3
    assert result["columns"] == 2
    assert "Revenue" in result["numeric_columns"]
    assert "Country" in result["categorical_columns"]


def test_get_chart_columns():
    dataframe = pd.DataFrame(
        {
            "Country": ["India", "USA", "UK"],
            "Revenue": [100, 200, 150],
        }
    )

    category, numeric = get_chart_columns(dataframe)

    assert category == "Country"
    assert numeric == "Revenue"