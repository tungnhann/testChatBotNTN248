import os
import requests
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# 5 Curated Sections
TARGET_SECTIONS = [
    26324076807315, # Youtube & Other Video Platforms
    26398357451923, # Getting Started
    26318828341267, # Quick Start Guide
    26319191493267, # Billing & Account Management
    26319049025683  # HW & Player Setup
]

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all('img'):
        if not img.get('alt'):
            img['alt'] = 'Image'
    markdown_text = md(str(soup), heading_style="ATX")
    return markdown_text

def scrape_articles():
    print(f"Starting curated scrape for {len(TARGET_SECTIONS)} sections...")
    articles_fetched = 0
    
    for section_id in TARGET_SECTIONS:
        print(f"Fetching section: {section_id}...")
        url = f"https://support.optisigns.com/api/v2/help_center/en-us/sections/{section_id}/articles.json"
        
        while url:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error fetching {url}: {response.status_code}")
                break
                
            data = response.json()
            articles = data.get("articles", [])
            
            for article in articles:
                article_id = article["id"]
                title = article["title"]
                body = article["body"]
                
                if not body:
                    continue
                    
                slug = slugify(title)
                filename = f"{article_id}-{slug}.md"
                filepath = os.path.join(DATA_DIR, filename)
                
                markdown_content = f"# {title}\n\n"
                markdown_content += f"**Article URL:** {article['html_url']}\n\n"
                markdown_content += html_to_markdown(body)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                
                articles_fetched += 1
                
            url = data.get("next_page")

    print(f"Done! Saved {articles_fetched} curated articles to '{DATA_DIR}'.")
    return articles_fetched

if __name__ == "__main__":
    scrape_articles()
