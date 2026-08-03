import httpx
import streamlit as st

# -----------------------------
# Page Title
# -----------------------------
st.title("Hybrid GraphRAG Chatbot")


# -----------------------------
# Backend API URL
# -----------------------------
API_URL = "http://localhost:8000/chat"


# -----------------------------
# User Input
# -----------------------------
query = st.text_input("Ask a Question")


# -----------------------------
# Query Processing
# -----------------------------
if query:
    with st.spinner("Retrieving and generating answer..."):
        try:
            payload = {"query": query}

            response = httpx.post(API_URL, json=payload, timeout=60.0)

            if response.status_code == 200:
                data = response.json()

                st.subheader("Answer")

                st.write(data["answer"])

                st.subheader("Sources")

                for source in data["citations"]:
                    st.write(f"- {source}")

            else:
                st.error(f"Backend Error: {response.status_code}")

        except Exception as error:
            st.error(f"Connection Failed: {error}")
