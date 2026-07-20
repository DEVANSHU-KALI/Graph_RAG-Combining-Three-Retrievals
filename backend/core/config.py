# backend/core/config.py

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# =========================
# NEO4J CONFIG
# =========================
NEO4J_USERNAME: str | None = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD: str | None = os.getenv("NEO4J_PASSWORD")
NEO4J_URL: str | None = os.getenv("NEO4J_URL")

# =========================
# OPENROUTER CONFIG
# =========================
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")

# =========================
# GEMINI CONFIG
# =========================
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

# =========================
# GROQ CONFIG
# =========================
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")


# =========================
# LANGSMITH CONFIG
# =========================
LANGCHAIN_TRACING_V2: str | None = os.getenv("LANGCHAIN_TRACING_V2")

LANGCHAIN_API_KEY: str | None = os.getenv("LANGCHAIN_API_KEY")

LANGCHAIN_PROJECT: str | None = os.getenv("LANGCHAIN_PROJECT")
