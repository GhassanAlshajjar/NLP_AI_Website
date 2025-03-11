from .file_handler import extract_text
from .plagiarism_checker import calculate_similarity
from collections import Counter
import re

def clean_text(text):
    """Lowercase, remove punctuation, and extra spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def compare_documents(doc1, doc2):
    """
    Compares two uploaded documents for similarity.
    Returns:
      - similarity_score (float): Percentage similarity.
      - extracted_text1 (str): Text extracted from document 1.
      - extracted_text2 (str): Text extracted from document 2.
      - word_comparison (dict): Word statistics between the two docs.
    """
    extracted_text1 = clean_text(extract_text(doc1))
    extracted_text2 = clean_text(extract_text(doc2))

    similarity_score = calculate_similarity(extracted_text1, extracted_text2)

    words1 = Counter(extracted_text1.split())
    words2 = Counter(extracted_text2.split())

    # Common words count (total occurrences, not just unique words)
    common_words = sum((words1 & words2).values())

    # Unique words count (words only appearing in one document)
    unique_words_doc1 = sum((words1 - words2).values())
    unique_words_doc2 = sum((words2 - words1).values())

    word_comparison = {
        "total_words_doc1": sum(words1.values()),
        "total_words_doc2": sum(words2.values()),
        "common_words": common_words,
        "unique_words_doc1": unique_words_doc1,
        "unique_words_doc2": unique_words_doc2
    }

    return similarity_score, extracted_text1, extracted_text2, word_comparison
