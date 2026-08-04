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
