import os
import glob
import json
import time
import hashlib
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

DATA_DIR = "data"
STATE_FILE = "sync_state.json"

SYSTEM_PROMPT = """You are OptiBot, a helpful AI customer support assistant for OptiSigns.
Your goal is to answer questions based strictly on the provided knowledge base.
If the answer is not in the knowledge base, politely say that you don't know and offer to connect them to human support.
Be concise and professional.
"""

def get_all_remote_files():
    """Lấy danh sách các file đã upload trên Gemini File API."""
    files = []
    try:
        for f in genai.list_files():
            files.append(f)
    except Exception as e:
        logging.error(f"Error listing files: {e}")
    return files

def upload_files_to_gemini():
    """Upload new/updated markdown files to Gemini."""
    if not API_KEY:
        logging.warning("GEMINI_API_KEY not found in environment.")
        return
        
    md_files = glob.glob(f"{DATA_DIR}/*.md")
    logging.info(f"Found {len(md_files)} files. Syncing to Gemini...")
    
    # Load state
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            
    added = 0
    updated = 0
    skipped = 0
    
    for filepath in md_files:
        filename = os.path.basename(filepath)
        
        # Read file and generate hash
        with open(filepath, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Delta check
        if filename in state and state[filename].get("hash") == file_hash:
            skipped += 1
            continue
            
        # If hash is different and file exists in state -> Update (Delete old file first)
        if filename in state:
            old_gemini_name = state[filename].get("gemini_name")
            if old_gemini_name:
                logging.info(f"Deleting old version of {filename} ({old_gemini_name})")
                try:
                    genai.delete_file(old_gemini_name)
                except Exception as e:
                    logging.warning(f"Could not delete old file {old_gemini_name}: {e}")
            updated += 1
        else:
            added += 1
            
        logging.info(f"Uploading {filename}...")
        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(path=filepath, display_name=filename)
            
            # Save to state
            state[filename] = {
                "hash": file_hash,
                "gemini_uri": uploaded_file.uri,
                "gemini_name": uploaded_file.name
            }
        except Exception as e:
            logging.error(f"Error uploading {filename}: {e}")
            if filename in state:
                updated -= 1
            else:
                added -= 1
            
    # Save state
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
        
    logging.info(f"Sync complete. Added: {added}, Updated: {updated}, Skipped: {skipped}")

def ask_assistant(question):
    if not API_KEY:
        logging.error("No API key.")
        return
    
    logging.info("Setting up model...")
    files = get_all_remote_files()
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    logging.info(f"Asking: {question}")
    contents = files + [question]
    response = model.generate_content(contents)
    
    print("\n--- OPTIBOT ---")
    print(response.text)
    print("---------------\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upload_files_to_gemini()
