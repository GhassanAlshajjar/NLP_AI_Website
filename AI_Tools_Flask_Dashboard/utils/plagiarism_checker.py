from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(text1, text2):
    """
    Calculates the similarity between two texts using cosine similarity.
    """
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()

    similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return similarity * 100  # Convert to percentage
