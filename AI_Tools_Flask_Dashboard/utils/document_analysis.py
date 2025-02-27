from .file_handler import extract_text
from .plagiarism_checker import calculate_similarity
from collections import Counter

def compare_documents(doc1, doc2):
    """
    Compares two uploaded documents for similarity.
    Returns:
      - similarity_score (float): Percentage similarity.
      - extracted_text1 (str): Text extracted from document 1.
      - extracted_text2 (str): Text extracted from document 2.
      - word_comparison (dict): Word statistics between the two docs.
    """
    extracted_text1 = extract_text(doc1)
    extracted_text2 = extract_text(doc2)

    similarity_score = calculate_similarity(extracted_text1, extracted_text2)

    words1 = Counter(extracted_text1.lower().split())
    words2 = Counter(extracted_text2.lower().split())

    common_words = set(words1.keys()) & set(words2.keys())

    word_comparison = {
        "total_words_doc1": sum(words1.values()),
        "total_words_doc2": sum(words2.values()),
        "common_words": len(common_words),
        "unique_words_doc1": len(words1.keys() - words2.keys()),
        "unique_words_doc2": len(words2.keys() - words1.keys())
    }

    return similarity_score, extracted_text1, extracted_text2, word_comparison
