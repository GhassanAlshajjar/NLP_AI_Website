import requests
import re

def preprocess_text(text, max_words=30):
    """
    Prepares text for search by removing excessive whitespace and limiting word count.
    """
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces and newlines
    words = text.split()[:max_words]  # Limit to first `max_words` words
    return " ".join(words)

def search_web_plagiarism(query, api_key, cx):
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    processed_query = preprocess_text(query)  # Apply preprocessing
    print(f"🔍 [DEBUG] Function Called! Searching for: {processed_query}")  # Ensure function is called
    
    params = {
        'key': api_key,
        'cx': cx,
        'q': processed_query
    }

    try:
        response = requests.get(search_url, params=params)
        print(f"📡 [DEBUG] API Status Code: {response.status_code}")  # Log HTTP status
        print(f"📜 [DEBUG] Raw Response: {response.text}")  # Log raw response

        response.raise_for_status()
        results = response.json()

        matches = []
        for item in results.get("items", []):
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            
            if title and link:
                matches.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })

        print(f"✅ [DEBUG] Found {len(matches)} results.")  # Debugging output
        return matches
    except requests.exceptions.RequestException as e:
        print(f"❌ [DEBUG] Plagiarism API Error: {e}")
        return []
