import os

import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# Load local environment variables.
# Streamlit Cloud secrets can be used as a fallback.
load_dotenv()


def get_model():
    """
    Initialize and return the configured Gemini model.
    """
    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or st.secrets.get("GOOGLE_API_KEY", "")
    )

    model_name = (
        os.getenv("GEMINI_MODEL")
        or st.secrets.get(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        )
    )

    if not api_key:
        raise ValueError(
            "Google API key is missing. Add GOOGLE_API_KEY "
            "to your local .env file or deployment secrets."
        )

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0,
        max_retries=2,
        timeout=60,
    )