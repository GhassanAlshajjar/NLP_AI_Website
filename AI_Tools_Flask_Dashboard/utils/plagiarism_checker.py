from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import numpy as np
import re

def calculate_similarity(text1, text2):
    """
    Calculates the similarity between two texts using cosine similarity.
    """
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()

    similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return similarity * 100

def clean_text(text):
    """Lowercase, remove special characters, and extra spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def calculate_plagiarism_score(text, matches):
    """
    Improved plagiarism detection:
    - Uses total word matches instead of averaging small snippets.
    - Adjusts similarity based on snippet relevance.
    """
    if not text or not matches:
        return 0

    text = clean_text(text)
    total_words = len(text.split())
    matched_texts = [clean_text(result["snippet"]) for result in matches]

    # Remove empty or very short matches (avoids bias from weak results)
    matched_texts = [m for m in matched_texts if len(m.split()) > 3]

    if not matched_texts:
        return 0  # No valid matched snippets found

    # TF-IDF Similarity Calculation
    vectorizer = TfidfVectorizer().fit_transform([text] + matched_texts)
    cosine_similarities = (vectorizer * vectorizer.T).toarray()[0][1:]

    # SequenceMatcher Similarity
    seq_similarities = [SequenceMatcher(None, text, match).ratio() for match in matched_texts]

    # **New Approach: Sum the Total Matched Word Count**
    total_matched_words = sum(len(match.split()) for match in matched_texts)
    word_match_ratio = total_matched_words / total_words  # % of words that match snippets

    # Weighted Similarity Calculation
    weighted_similarities = []
    for match, cos_sim, seq_sim in zip(matched_texts, cosine_similarities, seq_similarities):
        match_length = len(match.split())
        weight = match_length / total_words  # Snippet impact based on length
        weighted_similarities.append(((cos_sim + seq_sim) / 2) * weight)

    # Final Score: **Boost weight of longer matches**
    plagiarism_score = (sum(weighted_similarities) + word_match_ratio * 0.5) * 100  
    return min(round(plagiarism_score, 2), 100)



