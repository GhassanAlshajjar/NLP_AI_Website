import requests
import re
import time

# Cache to store already searched queries (to avoid duplicate searches)
plagiarism_cache = {}

def preprocess_text(text):
    """
    Cleans and processes text for search queries.
    Removes extra spaces, converts to lowercase, and limits to a reasonable length.
    """
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def search_web_plagiarism(query, api_key, cx, max_retries=2):
    """
    Searches for potential plagiarism using Google Custom Search API.
    - Uses full document search to minimize API calls.
    - Implements a retry limit to prevent infinite loops on rate limit errors.
    """
    search_url = "https://www.googleapis.com/customsearch/v1"
    processed_query = preprocess_text(query)

    # Avoid duplicate API calls (cache optimization)
    if processed_query in plagiarism_cache:
        print(f"🔄 [CACHE] Using cached results for: {processed_query}")
        return plagiarism_cache[processed_query]

    print(f"🔍 [DEBUG] Searching entire document for plagiarism...")

    params = {
        'key': api_key,
        'cx': cx,
        'q': processed_query
    }

    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(search_url, params=params)
            print(f"📡 [DEBUG] API Response Status: {response.status_code}")

            if response.status_code == 429:
                print(f"⚠️ [DEBUG] Rate limit exceeded. Attempt {retries + 1} of {max_retries}.")
                retries += 1
                time.sleep(2)
                continue

            response.raise_for_status()
            results = response.json()

            all_matches = []
            for item in results.get("items", []):
                match = {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                }
                all_matches.append(match)

            # Store in cache
            plagiarism_cache[processed_query] = all_matches

            print(f"✅ [DEBUG] Total Matches Found: {len(all_matches)}")
            return all_matches

        except requests.exceptions.RequestException as e:
            print(f"❌ [DEBUG] API Request Failed: {e}")
            return []

    print("🚨 [ERROR] Maximum retry attempts reached. Skipping this search.")
    return []
