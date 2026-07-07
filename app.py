import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
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
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    return model, files

with st.spinner("Connecting to knowledge base..."):
    model, context_files = setup_model()

# Image uploader in sidebar
st.sidebar.title("Attachments")
uploaded_file = st.sidebar.file_uploader("Upload a screenshot/image", type=["png", "jpg", "jpeg"])

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("image"):
            st.image(message["image"], width=300)

# User input
if prompt := st.chat_input("How do I add a YouTube video?"):
    img_obj = None
    if uploaded_file is not None:
        img_obj = Image.open(uploaded_file)

    st.session_state.messages.append({"role": "user", "content": prompt, "image": img_obj})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_obj:
            st.image(img_obj, width=300)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Construct context with uploaded files and conversation history
            contents = context_files.copy()
            for msg in st.session_state.messages:
                role = "user" if msg["role"] == "user" else "model"
                parts = [msg["content"]]
                if msg.get("image"):
                    parts.append(msg["image"])
                contents.append({"role": role, "parts": parts})
                
            try:
                response = model.generate_content(contents)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"An error occurred: {e}")
