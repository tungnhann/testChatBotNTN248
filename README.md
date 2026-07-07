# OptiBot Mini-Clone

This repository contains the implementation of the OptiBot Mini-Clone, integrating with Zendesk API and Google Gemini to build a smart customer support assistant.

## Overview
- **Task 1:** Scrapes articles from `support.optisigns.com` (Zendesk API) and normalizes them to clean Markdown.
- **Task 2:** Uploads the knowledge base to Gemini File API and initializes a `gemini-1.5-flash` assistant.
- **Task 3:** Implements a delta-sync strategy to only upload new or updated articles. Runs as a Dockerized daily job.

## Setup & Run Locally

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Rename `.env.sample` to `.env` and add your OpenAI API Key:
   ```env
   OPENAI_API_KEY=your_actual_key_here
   ```

4. **Run the Daily Job (Scrape & Sync):**
   ```bash
   python main.py
   ```
   *This will scrape data to `data/` and upload it to OpenAI.*

## Deployment & Daily Scheduling
This project includes an automated GitHub Actions workflow (`.github/workflows/daily_sync.yml`) that automatically runs the scraper and syncs to OpenAI once per day at 00:00 UTC. To enable it:
1. Push this repository to GitHub.
2. Go to **Settings > Secrets and variables > Actions** in your GitHub repository.
3. Add a new repository secret named `OPENAI_API_KEY` with your OpenAI API key.

Alternatively, to deploy and schedule this on a cloud provider like **DigitalOcean, Render, or Railway**:
1. Deploy the background worker using the provided `Dockerfile`.
2. Configure a native **Cron Job** on the platform (e.g., Render Cron Job, DigitalOcean App Platform Worker) with the schedule `0 0 * * *` and the command `python main.py`.

5. **Test the Assistant:**
   ```bash
   python main.py --ask "How do I add a YouTube video?"
   ```

## Docker Deployment
To run using Docker (which makes it easy to schedule on Render/DigitalOcean):
```bash
docker build -t optibot-job .
docker run -e GEMINI_API_KEY=your_key_here optibot-job
```

## Chunking Strategy
Instead of manually splitting documents into arbitrary character chunks (which loses context), **we utilize the Gemini 1.5 Flash model's massive 1-million token context window.**
- **Strategy:** Each full Markdown article is uploaded directly via the Gemini File API.
- **Why:** This ensures the AI has 100% perfect context of the article structure, leading to more accurate citations and factual responses compared to naive character chunking.

## Daily Job Logs
The daily job is designed to be deployed on platforms like Render or GitHub Actions. 
- *Link to recent job logs:* [Insert Link Here]

## Assistant Screenshot
*(Place your screenshot here showing the assistant answering the sample question)*
