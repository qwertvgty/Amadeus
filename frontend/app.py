"""LifeOS Frontend - Streamlit Chat UI."""

import streamlit as st
import httpx

API_BASE = "http://localhost:12345/api"

st.set_page_config(page_title="LifeOS", page_icon="🧠", layout="centered")
st.title("🧠 LifeOS - Personal AI Assistant")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask LifeOS anything..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = httpx.post(
                    f"{API_BASE}/chat",
                    json={
                        "user_id": "default_user",
                        "session_id": "default_session",
                        "message": prompt,
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["reply"]
            except Exception as e:
                reply = f"Error connecting to backend: {e}"

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
