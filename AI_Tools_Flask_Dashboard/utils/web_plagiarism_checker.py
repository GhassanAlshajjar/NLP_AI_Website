import requests

def search_web_plagiarism(query, api_key, cx):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cx,
        'q': query
    }
    response = requests.get(search_url, params=params)

    if response.status_code == 200:
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

        return matches
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []
