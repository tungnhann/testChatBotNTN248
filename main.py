import os
import sys
import datetime
import logging
from scraper import scrape_articles
from vector_store import upload_files_to_gemini, ask_assistant

# Configure Logging to output to both Console and sync.log file
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler("sync.log", mode='a', encoding='utf-8')
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

def run_daily_job():
    logging.info("Starting Daily Job...")
    
    # Step 1: Re-scrape
    logging.info("--- STEP 1: FETCH DATA FROM ZENDESK ---")
    scrape_articles()
    
    # Step 2: Upload delta
    logging.info("--- STEP 2: SYNC DATA TO GEMINI ---")
    upload_files_to_gemini()
    
    logging.info("Daily Job Finished!")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "How do I add a YouTube video?"
        ask_assistant(question)
    else:
        # Default behavior: run the daily job once and exit 0
        run_daily_job()
