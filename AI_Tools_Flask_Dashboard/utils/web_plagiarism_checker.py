import requests
import re

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

def search_web_plagiarism(text, api_key, cx, max_queries=3):
    """
    Searches multiple key phrases instead of the full document to improve results.
    - Selects diverse text samples for broader matches.
    """
    search_url = "https://www.googleapis.com/customsearch/v1"
    sentences = text.split(". ")[:max_queries]  # Select first few key sentences

    all_matches = []
    for sentence in sentences:
        processed_query = preprocess_text(sentence)

        # Avoid redundant API calls
        if processed_query in plagiarism_cache:
            print(f"🔄 [CACHE] Using cached results for: {processed_query}")
            all_matches.extend(plagiarism_cache[processed_query])
            continue

        params = {'key': api_key, 'cx': cx, 'q': processed_query}

        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            results = response.json()

            matches = [
                {"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")}
                for item in results.get("items", [])
            ]

            plagiarism_cache[processed_query] = matches  # Store in cache
            all_matches.extend(matches)

        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Failed: {e}")
            continue  # Continue to next query if API fails

    return all_matches


