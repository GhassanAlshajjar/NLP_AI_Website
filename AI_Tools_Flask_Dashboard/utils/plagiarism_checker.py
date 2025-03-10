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
    Uses NLP methods (TF-IDF & Sequence Matching) to improve plagiarism detection.
    Returns a percentage score indicating the likelihood of plagiarism.
    """
    if not text or not matches:
        return 0

    text = clean_text(text)
    total_words = len(text.split())
    matched_texts = [clean_text(result["snippet"]) for result in matches]

    # Ensure no empty matches are included
    matched_texts = [m for m in matched_texts if m]

    if not matched_texts:
        return 0  # No valid matched snippets found

    # TF-IDF Similarity
    vectorizer = TfidfVectorizer().fit_transform([text] + matched_texts)
    cosine_similarities = (vectorizer * vectorizer.T).toarray()[0][1:]

    # SequenceMatcher Similarity
    seq_similarities = [SequenceMatcher(None, text, match).ratio() for match in matched_texts]

    # Ensure at least one similarity value exists
    if not cosine_similarities.size or not seq_similarities:
        return 0

    # Weighted average (cosine similarity & sequence matching)
    avg_similarity = np.mean(cosine_similarities + seq_similarities)

    # Convert to percentage and cap at 100%
    plagiarism_score = round(avg_similarity * 100, 2)
    return min(plagiarism_score, 100)
