# Frontend Script Explanation

This document explains the web user interface (UI) of the application: `app.py`. This script handles the visual interaction layer, allowing users to type questions and view responses along with source citations.

---

## 1. `app.py`

### What Does This Script Do?
The `app.py` script builds and runs a **Streamlit** web application. Its primary responsibilities are:
1. **Rendering the UI:** Displays the page title and a text input field for the user's question.
2. **Sending API Requests:** Transmits the user's query as a JSON payload to our backend FastAPI server using `httpx`.
3. **Displaying Results:** Parses the backend's response and renders the generated answer and the source citations in a formatted layout.
4. **Error Handling:** Gracefully handles server timeouts, connection failures, and API errors, displaying user-friendly alerts.

---

### Why Do We Need It?
A backend API server (`main.py`) is designed for machine-to-machine communication. To make the chatbot usable by human users, we need a visual chat interface. **Streamlit** is a Python framework that lets developers build clean, reactive web interfaces in pure Python with zero HTML, CSS, or JavaScript boilerplate.

---

### Code Breakdown

#### A. Imports & UI Header Setup
```python
import httpx
import streamlit as st

# Page Title
st.title("Hybrid GraphRAG Chatbot")
```
- **`httpx`:** A modern HTTP client library for Python. We use it to send asynchronous/synchronous network requests to our FastAPI backend.
- **`streamlit as st`:** The Streamlit library namespace.
- **`st.title`:** A Streamlit widget that renders a formatted `<h1>` title banner at the top of the webpage.

---

#### B. Backend Configuration & User Input
```python
# Backend API URL
API_URL = "http://localhost:8000/chat"

# User Input
query = st.text_input("Ask a Question")
```
- **`API_URL`:** The address pointing to our FastAPI server's chat endpoint.
- **`st.text_input("Ask a Question")`:** Renders a text box. When the user types a query and presses Enter, the string is assigned to the `query` variable, which triggers a page reload and executes the downstream code.

---

#### C. Request Processing & Loading Indicators
```python
if query:
    with st.spinner("Retrieving and generating answer..."):
        try:
            payload = {"query": query}

            response = httpx.post(API_URL, json=payload, timeout=60.0)
```