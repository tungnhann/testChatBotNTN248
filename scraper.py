import os
import re
import json
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

API_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json"
DATA_DIR = "data"

def clean_html(html_content):
    """Clean HTML content if necessary before Markdown conversion."""
    if not html_content:
        return ""
    # Zendesk API 'body' is usually clean from nav/ads. 
    # We can use BeautifulSoup if we want to remove specific tags.
    soup = BeautifulSoup(html_content, "html.parser")
    return str(soup)

def html_to_markdown(html_content):
    """Convert HTML to clean Markdown, preserving links and code blocks."""
    clean_content = clean_html(html_content)
    # ATX heading style (## Heading) instead of UNDERLINED
    markdown = md(clean_content, heading_style="ATX", code_language="")
    return markdown.strip()

def slugify(text):
    """Create a URL-friendly slug from a string."""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def scrape_articles(limit=50):
    """Scrape articles from Zendesk API and save as Markdown files."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    url = API_URL
    articles_fetched = 0
    
    print(f"Fetching data from: {url}")
    
    while url and articles_fetched < limit:
        print(f"Loading: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get("articles", [])
        
        for article in articles:
            article_id = article["id"]
            title = article["title"] or article["name"]
            body = article["body"]
            
            if not body:
                continue
                
            slug = slugify(title)
            filename = f"{article_id}-{slug}.md"
            filepath = os.path.join(DATA_DIR, filename)
            
            # Formatting the markdown file
            markdown_content = f"# {title}\n\n"
            markdown_content += f"**Article URL:** {article['html_url']}\n\n"
            markdown_content += html_to_markdown(body)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            articles_fetched += 1
            if articles_fetched >= limit:
                break
                
        url = data.get("next_page")

    print(f"Done! Saved {articles_fetched} articles to '{DATA_DIR}'.")
    return articles_fetched

if __name__ == "__main__":
    # Fetch 50 articles as sample
    scrape_articles(limit=50)
