import os
import sys
import datetime
from scraper import scrape_articles
from vector_store import upload_files_to_gemini, ask_assistant

def run_daily_job():
    print(f"[{datetime.datetime.now()}] Starting Daily Job...")
    
    # Bước 1: Re-scrape
    print("\n--- STEP 1: FETCH DATA FROM ZENDESK ---")
    scrape_articles(limit=50)
    
    # Bước 2: Upload delta
    print("\n--- STEP 2: SYNC DATA TO GEMINI ---")
    upload_files_to_gemini()
    
    print(f"\n[{datetime.datetime.now()}] Daily Job Finished!")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "How do I add a YouTube video?"
        ask_assistant(question)
    else:
        # Default behavior: run the daily job once and exit 0
        run_daily_job()
