import os
import glob
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment.")
else:
    genai.configure(api_key=API_KEY)

DATA_DIR = "data"
SYNC_STATE_FILE = "sync_state.json"

SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""

def load_sync_state():
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sync_state(state):
    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def upload_files_to_gemini():
    """Uploads markdown files to Gemini via File API."""
    md_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    state = load_sync_state()
    uploaded_files = []
    
    added = 0
    updated = 0
    skipped = 0
    
    print(f"Found {len(md_files)} files. Syncing to Gemini...")
    
    for filepath in md_files:
        filename = os.path.basename(filepath)
        mod_time = os.path.getmtime(filepath)
        
        # Simple delta check
        if filename in state and state[filename].get("mtime") == mod_time:
            skipped += 1
            # Retrieve existing file reference if needed, 
            # but for Gemini we might need to fetch the list of uploaded files from API.
            continue
            
        print(f"Uploading {filename}...")
        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(path=filepath, display_name=filename)
            
            # Save to state
            state[filename] = {
                "mtime": mod_time,
                "gemini_uri": uploaded_file.uri,
                "gemini_name": uploaded_file.name
            }
            
            if filename in state:
                updated += 1
            else:
                added += 1
                
            time.sleep(1) # Prevent rate limiting
        except Exception as e:
            print(f"Error uploading {filename}: {e}")
            
    save_sync_state(state)
    print(f"Sync complete. Added: {added}, Updated: {updated}, Skipped: {skipped}")
    
def get_all_remote_files():
    """Retrieve all files uploaded to Gemini API."""
    files = []
    for f in genai.list_files():
        files.append(f)
    return files

def ask_assistant(question):
    """Sanity check: ask the assistant a question."""
    print("Setting up model...")
    # Fetch all files to provide as context
    files = get_all_remote_files()
    if not files:
        print("No files found on Gemini. Please upload first.")
        return
        
    print(f"Using {len(files)} files as context.")
    
    # We use gemini-1.5-flash as it supports large context windows (up to 1M tokens)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    # Pass the question and the uploaded files as history/context
    print(f"Asking: {question}")
    contents = files + [question]
    
    response = model.generate_content(contents)
    print("\n--- RESPONSE ---\n")
    print(response.text)
    print("\n----------------\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "How do I add a YouTube video?"
        ask_assistant(question)
    else:
        upload_files_to_gemini()
