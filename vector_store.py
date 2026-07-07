import os
import glob
import json
import time
import hashlib
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENAI_API_KEY")

DATA_DIR = "data"
STATE_FILE = "sync_state.json"

SYSTEM_PROMPT = """You are OptiBot, a helpful AI customer support assistant for OptiSigns.
Your goal is to answer questions based strictly on the provided knowledge base (via the file_search tool).
If the answer is not in the knowledge base, politely say that you don't know and offer to connect them to human support.
Be concise and professional.
"""

def get_client():
    if not API_KEY:
        return None
    return OpenAI(api_key=API_KEY)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"metadata": {}, "files": {}}
    return {"metadata": {}, "files": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_assistant_id():
    state = load_state()
    return state.get("metadata", {}).get("assistant_id")

def upload_files_to_openai():
    client = get_client()
    if not client:
        logging.warning("OPENAI_API_KEY not found in environment.")
        return
        
    md_files = glob.glob(f"{DATA_DIR}/*.md")
    logging.info(f"Found {len(md_files)} files. Syncing to OpenAI...")
    
    state = load_state()
    meta = state.setdefault("metadata", {})
    files_state = state.setdefault("files", {})
    
    # 1. Setup Vector Store
    vector_store_id = meta.get("vector_store_id")
    if not vector_store_id:
        logging.info("Looking for existing Vector Store...")
        for vs in client.vector_stores.list(limit=50):
            if vs.name == "OptiSigns_Knowledge_Base":
                vector_store_id = vs.id
                logging.info(f"Found existing Vector Store: {vector_store_id}")
                break
                
        if not vector_store_id:
            logging.info("Creating new Vector Store...")
            vs = client.vector_stores.create(name="OptiSigns_Knowledge_Base")
            vector_store_id = vs.id
            
        meta["vector_store_id"] = vector_store_id
        save_state(state)
        
    # 2. Setup Assistant
    assistant_id = meta.get("assistant_id")
    if not assistant_id:
        logging.info("Looking for existing Assistant...")
        for asst in client.beta.assistants.list(limit=50):
            if asst.name == "OptiBot":
                assistant_id = asst.id
                logging.info(f"Found existing Assistant: {assistant_id}")
                break
                
        if not assistant_id:
            logging.info("Creating new Assistant...")
            assistant = client.beta.assistants.create(
                name="OptiBot",
                instructions=SYSTEM_PROMPT,
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            assistant_id = assistant.id
            
        meta["assistant_id"] = assistant_id
        save_state(state)
        
    added = 0
    updated = 0
    skipped = 0
    
    for filepath in md_files:
        filename = os.path.basename(filepath)
        
        with open(filepath, "rb") as f:
            content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
            
        if filename in files_state and files_state[filename].get("hash") == file_hash:
            skipped += 1
            continue
            
        # Delete old file if updating
        if filename in files_state:
            old_file_id = files_state[filename].get("file_id")
            if old_file_id:
                logging.info(f"Deleting old version of {filename} ({old_file_id})")
                try:
                    client.files.delete(old_file_id)
                except Exception as e:
                    logging.warning(f"Could not delete old file {old_file_id}: {e}")
            updated += 1
        else:
            added += 1
            
        logging.info(f"Uploading {filename}...")
        try:
            # Upload file to OpenAI
            with open(filepath, "rb") as f:
                uploaded_file = client.files.create(file=f, purpose="assistants")
            
            # Add to Vector Store
            client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=uploaded_file.id
            )
            
            files_state[filename] = {
                "hash": file_hash,
                "file_id": uploaded_file.id
            }
            # Save incrementally
            save_state(state)
        except Exception as e:
            logging.error(f"Error uploading {filename}: {e}")
            if filename in files_state:
                updated -= 1
            else:
                added -= 1
                
    logging.info(f"Sync complete. Added: {added}, Updated: {updated}, Skipped: {skipped}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upload_files_to_openai()
