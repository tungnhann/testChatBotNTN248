import os
import sys
import datetime
import logging
from scraper import scrape_articles
from vector_store import upload_files_to_openai

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
    logging.info("--- STEP 2: SYNC DATA TO OPENAI ---")
    upload_files_to_openai()
    
    logging.info("Daily Job Finished!")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        import time
        logging.info("Starting DEMO MODE: Running job every 60 seconds...")
        while True:
            run_daily_job()
            logging.info("Waiting 60 seconds for the next run...")
            time.sleep(60)
    else:
        # Default behavior: run the daily job once and exit 0
        run_daily_job()
