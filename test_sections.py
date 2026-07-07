import requests

categories_url = 'https://support.optisigns.com/api/v2/help_center/en-us/categories.json'
data = requests.get(categories_url).json()

for c in data.get('categories', []):
    print(f"--- Category: {c['name']} (ID: {c['id']}) ---")
    sections_url = f"https://support.optisigns.com/api/v2/help_center/en-us/categories/{c['id']}/sections.json"
    sec_data = requests.get(sections_url).json()
    for s in sec_data.get('sections', []):
        print(f"  Section: {s['name']} (ID: {s['id']})")
