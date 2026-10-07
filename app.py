import json

import pandas as pd
import streamlit as st
import plotly.express as px

from sqlalchemy import inspect

from database.connection import get_engine

from database.schema import (
    get_database_schema,
    get_table_names,
    get_table_details,
    search_schema,
    export_schema_json,
)

from database.explorer import (
    get_database_summary,
    get_table_preview,
    get_table_row_count,
)

from llm.sql_generator import generate_sql
from llm.sql_corrector import correct_sql

from sql.validator import (
    validate_sql,
    SQLValidationError,
)

from sql.executor import (
    execute_sql,
    SQLExecutionError,
)

from config.settings import (
    APP_NAME,
    APP_VERSION,
    MAX_HISTORY_ITEMS,
    SAMPLE_QUESTIONS_PATH,
)

from sql.formatter import format_sql

from analytics.insights import (
    analyze_dataframe,
    get_numeric_summary,
)

from analytics.visualizer import (
    create_bar_chart,
    create_line_chart,
)

from utils.helpers import (
    clean_question,
    truncate_text,
)

from utils.logger import logger

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 750;
            margin-bottom: 0;
        }

        .subtitle {
            color: #9CA3AF;
            font-size: 1rem;
            margin-top: 0.3rem;
        }

        .section-title {
            font-size: 1.3rem;
            font-weight: 650;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.25);
            padding: 14px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULT_STATE = {
    "generated_sql": "",
    "sql_explanation": "",
    "tables_used": [],
    "clarification_needed": False,
    "clarification_question": "",
    "last_question": "",
    "query_results": None,
    "query_error": "",
    "corrected_sql": "",
    "correction_explanation": "",
    "correction_attempted": False,
    "query_history": [],
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    f'<div class="main-title">🧠 {APP_NAME}</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Ask questions about your database in natural language '
    'and explore data using AI-generated SQL.'
    '</div>',
    unsafe_allow_html=True,
)

st.divider()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.title("QueryMind AI")
    st.caption("Natural Language to SQL")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Table Explorer",
            "Schema Search",
            "Relationships",
            "AI SQL Generator",
            "Query History",
        ],
        key="navigation_page",
    )

    st.divider()

    st.markdown("**Database**")
    st.write("SQLite — Chinook")

    st.caption("Explore tables, inspect relationships, "
               "and query your data.")


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def display_schema_download():
    """Display a download button for the database schema."""

    try:
        schema_json = export_schema_json()

        if isinstance(schema_json, (dict, list)):
            schema_json = json.dumps(
                schema_json,
                indent=2,
                default=str,
            )

        st.download_button(
            label="Download schema as JSON",
            data=schema_json,
            file_name="chinook_schema.json",
            mime="application/json",
            key="download_schema_json",
        )

    except Exception as exc:
        st.warning(f"Could not export the schema: {exc}")


def clear_query_results():
    """Clear previously displayed query results."""

    st.session_state.query_results = None
    st.session_state.query_error = ""


def add_query_to_history(
    question,
    sql,
    dataframe,
    corrected=False,
):
    """Store a successful query in session history."""

    history_item = {
        "question": question,
        "sql": sql,
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "corrected": corrected,
    }

    st.session_state.query_history.insert(
        0,
        history_item,
    )

    # Keep only the latest 20 queries.
    st.session_state.query_history = (
        st.session_state.query_history[:MAX_HISTORY_ITEMS]
    )


def render_sql_results():
    """Render the most recently executed SQL results."""

    dataframe = st.session_state.query_results

    if dataframe is None:
        return

    st.subheader("Query Results")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "Rows",
            len(dataframe),
        )

    with metric_col2:
        st.metric(
            "Columns",
            len(dataframe.columns),
        )

    with metric_col3:
        st.metric(
            "Missing Values",
            int(dataframe.isna().sum().sum()),
        )

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    # ----------------------------------------------
    # AUTOMATIC INSIGHTS
    # ----------------------------------------------

    st.markdown("### Automatic Insights")

    analysis = analyze_dataframe(dataframe)

    for insight in analysis["insights"]:
        st.write(f"• {insight}")

    # ----------------------------------------------
    # VISUALIZATION
    # ----------------------------------------------

    st.markdown("### Visualization")

    bar_chart = create_bar_chart(dataframe)

    if bar_chart is not None:
        st.plotly_chart(
            bar_chart,
            use_container_width=True,
        )
    else:
        line_chart = create_line_chart(dataframe)

        if line_chart is not None:
            st.plotly_chart(
                line_chart,
                use_container_width=True,
            )
        else:
            st.info(
                "A suitable automatic chart could not be created "
                "for this result."
            )

    if dataframe.attrs.get("truncated", False):

        st.info(
            "The result was limited to the maximum number "
            "of rows. Refine your question for a smaller "
            "result."
        )

    # ----------------------------------------------
    # NUMERICAL SUMMARY
    # ----------------------------------------------

    summary = get_numeric_summary(dataframe)

    if not summary.empty:

        with st.expander("Numerical Summary"):

            st.dataframe(
                summary,
                use_container_width=True,
            )

    # ----------------------------------------------
    # DOWNLOAD
    # ----------------------------------------------

    csv_data = dataframe.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download results as CSV",
        data=csv_data,
        file_name="querymind_results.csv",
        mime="text/csv",
        key="download_query_results",
    )

def load_sample_questions():
    """Load example questions from the JSON file."""

    try:
        with open(
            SAMPLE_QUESTIONS_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        questions = data.get("questions", [])

        if not isinstance(questions, list):
            logger.error(
                "Sample questions must be stored as a list."
            )
            return []

        return questions

    except FileNotFoundError:
        logger.error(
            "Sample questions file not found: %s",
            SAMPLE_QUESTIONS_PATH,
        )
        return []

    except json.JSONDecodeError as exc:
        logger.error(
            "Invalid sample questions JSON: %s",
            exc,
        )
        return []

    except OSError as exc:
        logger.error(
            "Unable to read sample questions: %s",
            exc,
        )
        return []
    
def render_result_chart(dataframe):
    """Create a simple automatic visualization for query results."""

    if dataframe is None or dataframe.empty:
        return

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = dataframe.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    if not numeric_columns or not categorical_columns:
        return

    category_column = categorical_columns[0]
    numeric_column = numeric_columns[0]

    chart_data = dataframe[
        [category_column, numeric_column]
    ].dropna()

    if chart_data.empty:
        return

    st.subheader("Visualization")

    fig = px.bar(
        chart_data.head(20),
        x=category_column,
        y=numeric_column,
        title=f"{numeric_column} by {category_column}",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# --------------------------------------------------
# PAGE 1: OVERVIEW
# --------------------------------------------------

if page == "Overview":

    st.header("Database Overview")

    st.write(
        "Welcome to QueryMind AI. Use this workspace to explore "
        "the Chinook database and generate SQL from natural-language "
        "questions."
    )

    try:
        summary = get_database_summary()
        table_names = get_table_names()

        if isinstance(summary, dict):
            st.subheader("Database Summary")

            # Display summary information without assuming
            # a particular dictionary structure.
            st.json(summary)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Tables", len(table_names))

        with col2:
            st.metric(
                "Database",
                "Chinook SQLite",
            )

        st.subheader("Available Tables")

        if table_names:
            st.dataframe(
                pd.DataFrame({"Table Name": table_names}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No tables were found in the database.")

        display_schema_download()

    except Exception as exc:
        st.error(
            "Could not load the database overview. "
            f"Check your database connection and explorer functions. "
            f"Details: {exc}"
        )


# --------------------------------------------------
# PAGE 2: TABLE EXPLORER
# --------------------------------------------------

elif page == "Table Explorer":

    st.header("Table Explorer")

    try:
        table_names = get_table_names()

        if not table_names:
            st.warning("No database tables are available.")

        else:
            selected_table = st.selectbox(
                "Select a table",
                table_names,
                key="selected_table",
            )

            preview_limit = st.slider(
                "Preview row limit",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
            )

            if selected_table:
                col1, col2 = st.columns(2)

                with col1:
                    row_count = get_table_row_count(selected_table)
                    st.metric("Total Rows", row_count)

                with col2:
                    st.metric("Preview Limit", preview_limit)

                st.subheader(f"Preview: {selected_table}")

                preview_df = get_table_preview(
                    selected_table,
                    limit=preview_limit,
                )

                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.subheader("Table Schema")

                table_details = get_table_details(selected_table)

                st.json(table_details, expanded=True)

                if isinstance(preview_df, pd.DataFrame):
                    csv_data = preview_df.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        "Download table preview as CSV",
                        data=csv_data,
                        file_name=f"{selected_table}_preview.csv",
                        mime="text/csv",
                    )

    except Exception as exc:
        st.error(f"Could not load table information: {exc}")


# --------------------------------------------------
# PAGE 3: SCHEMA SEARCH
# --------------------------------------------------

elif page == "Schema Search":

    st.header("Schema Search")

    st.write(
        "Search table names, column names, and other schema details "
        "to understand the structure of your database."
    )

    search_query = st.text_input(
        "Search tables or columns",
        placeholder="Example: customer, invoice, track, artist",
    )

    if st.button("Search Schema", type="primary"):

        if not search_query.strip():
            st.warning("Enter a search term first.")

        else:
            try:
                results = search_schema(search_query.strip())

                st.subheader("Search Results")

                if results:
                    if isinstance(results, pd.DataFrame):
                        st.dataframe(
                            results,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.write(results)
                else:
                    st.info("No matching schema information found.")

            except Exception as exc:
                st.error(f"Schema search failed: {exc}")

    st.divider()
    st.subheader("Complete Database Schema")

    if st.button("View Full Schema"):
        try:
            schema = get_database_schema()
            st.json(schema, expanded=False)

        except Exception as exc:
            st.error(f"Could not load the schema: {exc}")

    display_schema_download()


# --------------------------------------------------
# PAGE 4: RELATIONSHIPS
# --------------------------------------------------

elif page == "Relationships":

    st.header("Database Relationships")

    st.write(
        "Explore foreign-key relationships between tables. "
        "These relationships help determine how tables can be joined."
    )

    try:
        engine = get_engine()
        inspector = inspect(engine)

        relationships = []

        table_names = inspector.get_table_names()

        for table_name in table_names:

            foreign_keys = inspector.get_foreign_keys(table_name)

            for foreign_key in foreign_keys:

                source_columns = foreign_key.get(
                    "constrained_columns"
                ) or []

                referenced_table = foreign_key.get(
                    "referred_table"
                ) or ""

                referenced_columns = foreign_key.get(
                    "referred_columns"
                ) or []

                relationships.append(
                    {
                        "Source Table": table_name,
                        "Source Columns": ", ".join(
                            str(column)
                            for column in source_columns
                        ),
                        "Referenced Table": str(
                            referenced_table
                        ),
                        "Referenced Columns": ", ".join(
                            str(column)
                            for column in referenced_columns
                        ),
                    }
                )

        # ----------------------------------------------
        # DISPLAY RELATIONSHIPS
        # ----------------------------------------------

        if relationships:

            relationship_df = pd.DataFrame(
                relationships,
                columns=[
                    "Source Table",
                    "Source Columns",
                    "Referenced Table",
                    "Referenced Columns",
                ],
            )

            st.metric(
                "Foreign-Key Relationships",
                len(relationship_df),
            )

            st.dataframe(
                relationship_df,
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------
            # DOWNLOAD RELATIONSHIPS
            # ------------------------------------------

            csv_data = relationship_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download relationships as CSV",
                data=csv_data,
                file_name="chinook_relationships.csv",
                mime="text/csv",
            )

            # ------------------------------------------
            # RELATIONSHIP DETAILS
            # ------------------------------------------

            st.subheader("Relationship Details")

            for relationship in relationships:

                st.markdown(
                    f"**{relationship['Source Table']}"
                    f".{relationship['Source Columns']}**"
                    f" → "
                    f"**{relationship['Referenced Table']}"
                    f".{relationship['Referenced Columns']}**"
                )

        else:

            st.info(
                "No foreign-key relationships were found "
                "in the database."
            )

        # ----------------------------------------------
        # COMPLETE SCHEMA
        # ----------------------------------------------

        with st.expander("View complete schema"):

            try:
                schema = get_database_schema()
                st.json(schema, expanded=False)

            except Exception as exc:
                st.warning(
                    f"Could not display complete schema: {exc}"
                )

    except Exception as exc:

        st.error(
            "Could not load database relationships."
        )

        st.exception(exc)


# --------------------------------------------------
# PAGE 5: AI SQL GENERATOR
# --------------------------------------------------

elif page == "AI SQL Generator":

    st.header("AI SQL Generator")

    st.write(
        "Write your question in plain English. QueryMind AI will "
        "generate SQL using the database schema."
    )

    # Load sample questions from data/samplequestions.json
    sample_questions = load_sample_questions()

    example_questions = [
        item["question"]
        for item in sample_questions
        if "question" in item
    ]

    selected_example = st.selectbox(
        "Try an example question",
        ["Choose an example..."] + example_questions,
    )

    default_question = (
        selected_example
        if selected_example != "Choose an example..."
        else ""
    )

    with st.form("sql_generation_form"):

        question = st.text_area(
            "Ask a question about your database",
            value=default_question,
            placeholder=(
                "Example: Which 10 customers have spent "
                "the most money?"
            ),
            height=110,
            max_chars=2000,
        )

        generate_button = st.form_submit_button(
            "Generate SQL",
            type="primary",
            use_container_width=True,
        )

    if generate_button:

        if not question.strip():
            st.warning("Enter a question before generating SQL.")

        else:
            clear_query_results()
            st.session_state.generated_sql = ""
            st.session_state.sql_explanation = ""
            st.session_state.tables_used = []
            st.session_state.clarification_needed = False
            st.session_state.clarification_question = ""
            st.session_state.last_question = question.strip()

            st.session_state.corrected_sql = ""
            st.session_state.correction_explanation = ""
            st.session_state.correction_attempted = False

            try:
                with st.spinner("Generating SQL with Gemini..."):
                    result = generate_sql(question.strip())

                st.session_state.generated_sql = result.sql
                st.session_state.sql_explanation = result.explanation
                st.session_state.tables_used = result.tables_used
                st.session_state.clarification_needed = (
                    result.clarification_needed
                )
                st.session_state.clarification_question = (
                    result.clarification_question
                )

            except Exception as exc:
                st.error(
                    "SQL generation failed. Check your Gemini API "
                    "configuration, model availability, and logs."
                )
                st.caption(f"Error details: {exc}")

    # ----------------------------------------------
    # DISPLAY GENERATED SQL
    # ----------------------------------------------

    generated_sql = st.session_state.generated_sql

    if generated_sql:

        st.divider()
        st.subheader("Generated SQL")

        st.code(generated_sql, language="sql")

        if st.session_state.clarification_needed:
            st.info(
                st.session_state.clarification_question
                or "The question needs clarification before execution."
            )

        else:
            if st.session_state.sql_explanation:
                st.subheader("Explanation")
                st.write(st.session_state.sql_explanation)

            if st.session_state.tables_used:
                st.subheader("Tables Used")
                st.write(", ".join(st.session_state.tables_used))

            # --------------------------------------
            # VALIDATE SQL
            # --------------------------------------

            st.subheader("SQL Safety Check")

            try:
                validated_sql = validate_sql(generated_sql)
                st.success("SQL passed the validator checks.")

                with st.expander("View normalized SQL"):
                    formatted_sql = format_sql(validated_sql)
                    st.code(formatted_sql, language="sql")

            except SQLValidationError as exc:
                validated_sql = None

                st.error(
                    "This generated SQL did not pass validation. "
                    "It cannot be executed."
                )
                st.warning(str(exc))

            # --------------------------------------
            # EXECUTE SQL
            # --------------------------------------

            if validated_sql:

                if st.button(
                    "Run SQL",
                    type="primary",
                    key="run_generated_sql",
                    use_container_width=True,
                ):

                    clear_query_results()

                    try:
                        # ------------------------------------------
                        # FIRST EXECUTION ATTEMPT
                        # ------------------------------------------

                        with st.spinner(
                            "Executing read-only SQL query..."
                        ):
                            dataframe = execute_sql(validated_sql)

                        st.session_state.query_results = dataframe
                        st.session_state.query_error = ""

                        add_query_to_history(
                            question=st.session_state.last_question,
                            sql=validated_sql,
                            dataframe=dataframe,
                            corrected=False,
                        )

                        st.success(
                            "Query executed successfully."
                        )

                    except SQLValidationError as exc:

                        st.session_state.query_error = str(exc)

                    except SQLExecutionError as exc:

                        error_message = str(exc)

                        st.session_state.query_error = error_message

                        # ------------------------------------------
                        # AUTOMATIC SQL CORRECTION
                        # ------------------------------------------

                        if not st.session_state.correction_attempted:

                            st.session_state.correction_attempted = True

                            st.warning(
                                "The generated SQL could not be executed."
                            )

                            st.info(
                                "QueryMind AI is analyzing the database "
                                "error and attempting to correct the SQL..."
                            )

                            try:

                                with st.spinner(
                                    "Gemini is correcting the SQL..."
                                ):

                                    correction = correct_sql(
                                        question=(
                                            st.session_state.last_question
                                        ),
                                        failed_sql=validated_sql,
                                        error_message=error_message,
                                    )

                                corrected_sql = correction.sql.strip()

                                st.session_state.corrected_sql = (
                                    corrected_sql
                                )

                                st.session_state.correction_explanation = (
                                    correction.explanation
                                )

                                # ----------------------------------
                                # VALIDATE CORRECTED SQL
                                # ----------------------------------

                                try:

                                    validated_corrected_sql = (
                                        validate_sql(corrected_sql)
                                    )

                                except SQLValidationError as validation_error:

                                    st.error(
                                        "Gemini produced corrected SQL, "
                                        "but the corrected query failed "
                                        "the safety validator."
                                    )

                                    st.warning(
                                        str(validation_error)
                                    )

                                    validated_corrected_sql = None

                                # ----------------------------------
                                # EXECUTE CORRECTED SQL
                                # ----------------------------------

                                if validated_corrected_sql:

                                    st.subheader(
                                        "Corrected SQL"
                                    )
                                    
                                    formatted_corrected_sql = format_sql(
                                        validated_corrected_sql
                                    )
                                    st.code(
                                        formatted_corrected_sql,
                                        language="sql",
                                    )

                                    if (
                                        st.session_state
                                        .correction_explanation
                                    ):
                                        st.write(
                                            st.session_state
                                            .correction_explanation
                                        )

                                    with st.spinner(
                                        "Executing corrected SQL..."
                                    ):

                                        corrected_dataframe = (
                                            execute_sql(
                                                validated_corrected_sql
                                            )
                                        )

                                    st.session_state.query_results = (
                                        corrected_dataframe
                                    )

                                    st.session_state.query_error = ""

                                    add_query_to_history(
                                        question=st.session_state.last_question,
                                        sql=validated_corrected_sql,
                                        dataframe=corrected_dataframe,
                                        corrected=True,
                                    )
                                    
                                    st.success(
                                        "Corrected SQL executed successfully."
                                    )

                            except (
                                SQLValidationError,
                                SQLExecutionError,
                            ) as correction_error:

                                st.error(
                                    "The automatic SQL correction "
                                    "could not be executed."
                                )

                                st.warning(
                                    str(correction_error)
                                )

                            except Exception as correction_error:

                                st.error(
                                    "The automatic SQL correction failed."
                                )

                                st.caption(
                                    f"Correction error: "
                                    f"{correction_error}"
                                )

                    except Exception as exc:

                        st.session_state.query_error = (
                            f"Unexpected execution error: {exc}"
                        )

                # ----------------------------------------------
                # DISPLAY ORIGINAL ERROR
                # ----------------------------------------------

                if st.session_state.query_error:

                    st.error(
                        f"Original query error: "
                        f"{st.session_state.query_error}"
                    )

                if st.session_state.query_error:
                    st.error(st.session_state.query_error)

                render_sql_results()

    else:
        st.info(
            "Generate a SQL query to see the SQL, its explanation, "
            "and the option to execute it."
        )

# --------------------------------------------------
# PAGE 6: QUERY HISTORY
# --------------------------------------------------

elif page == "Query History":

    st.header("Query History")

    st.write(
        "Review questions and SQL queries executed during "
        "this Streamlit session."
    )

    history = st.session_state.query_history

    if not history:

        st.info(
            "No queries have been executed yet. "
            "Go to AI SQL Generator and run a query."
        )

    else:

        st.metric(
            "Queries in History",
            len(history),
        )

        for index, item in enumerate(history):

            status = (
                "Corrected by AI"
                if item["corrected"]
                else "Executed directly"
            )

            with st.expander(
                f"{index + 1}. {item['question']}"
            ):

                st.caption(status)

                st.markdown("**SQL Query**")

                st.code(
                    item["sql"],
                    language="sql",
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Rows",
                        item["rows"],
                    )

                with col2:
                    st.metric(
                        "Columns",
                        item["columns"],
                    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "QueryMind AI | Natural Language to SQL | "
    "Python • Streamlit • SQLite • SQLGlot • Gemini"
)