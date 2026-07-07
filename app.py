import os
import streamlit as st
import google.generativeai as genai
from vector_store import get_all_remote_files, SYSTEM_PROMPT

# Configure API Key
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

st.set_page_config(page_title="OptiBot", page_icon="🤖")

st.title("🤖 OptiBot Assistant")
st.markdown("I am OptiBot, the customer-support bot for OptiSigns. Ask me anything!")

# Ensure API key is set
if not API_KEY:
    st.error("Missing GEMINI_API_KEY in environment variables.")
    st.stop()

@st.cache_resource
def setup_model():
    files = get_all_remote_files()
    if not files:
        st.warning("No files found on Gemini. Please run the daily job first.")
        st.stop()
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    return model, files

with st.spinner("Connecting to knowledge base..."):
    model, context_files = setup_model()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How do I add a YouTube video?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Construct context with uploaded files and conversation history
            contents = context_files.copy()
            for msg in st.session_state.messages:
                # Basic mapping to user/model roles for Gemini
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})
                
            response = model.generate_content(contents)
            st.markdown(response.text)
            
    st.session_state.messages.append({"role": "assistant", "content": response.text})
