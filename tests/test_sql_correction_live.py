from llm.sql_corrector import correct_sql


def test_live_sql_correction():

    result = correct_sql(
        question="Show the names of all artists.",
        failed_sql="SELECT ArtistName FROM Artist",
        error_message=(
            "no such column: ArtistName"
        ),
    )

    print("\nCorrected SQL:")
    print(result.sql)

    print("\nExplanation:")
    print(result.explanation)

    assert result.sql
    assert isinstance(result.explanation, str)