import os
import time
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
import io

from vector_store import get_client, get_assistant_id

load_dotenv()

st.set_page_config(page_title="OptiBot", page_icon="🤖")

st.title("🤖 OptiBot Assistant")
st.markdown("I am OptiBot, the customer-support bot for OptiSigns. Ask me anything!")

client = get_client()
if not client:
    st.error("Missing OPENAI_API_KEY in environment variables.")
    st.stop()

@st.cache_resource
def setup_assistant():
    ast_id = get_assistant_id()
    if not ast_id:
        st.warning("No Assistant found. Please run the daily job (python main.py) first.")
        st.stop()
    return ast_id

with st.spinner("Connecting to knowledge base..."):
    assistant_id = setup_assistant()

# Initialize Thread
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

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
    img_file_id = None
    
    if uploaded_file is not None:
        img_obj = Image.open(uploaded_file)
        # Upload image to OpenAI for Vision
        img_bytes = uploaded_file.getvalue()
        try:
            file_response = client.files.create(
                file=(uploaded_file.name, img_bytes, "image/png"),
                purpose="vision"
            )
            img_file_id = file_response.id
        except Exception as e:
            st.error(f"Error uploading image to OpenAI: {e}")

    # Render User Message immediately
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img_obj})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_obj:
            st.image(img_obj, width=300)

    # Call OpenAI
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Construct message payload for Assistants API
                if img_file_id:
                    content = [
                        {"type": "text", "text": prompt},
                        {"type": "image_file", "image_file": {"file_id": img_file_id}}
                    ]
                else:
                    content = prompt
                    
                # Add message to thread
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=content
                )
                
                # Run the thread
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=st.session_state.thread_id,
                    assistant_id=assistant_id
                )
                
                if run.status == 'completed': 
                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )
                    # The latest message is the first one in the list
                    latest_msg = messages.data[0]
                    reply = latest_msg.content[0].text.value
                    
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    st.error(f"Run failed with status: {run.status}")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
