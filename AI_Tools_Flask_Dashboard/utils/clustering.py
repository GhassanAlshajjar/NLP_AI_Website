import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def detect_metaphors(corpus_phrases, metaphor_phrases):
    # Generate embeddings
    from utils.embeddings import get_embeddings
    
    corpus_embeddings = get_embeddings(corpus_phrases)
    metaphor_embeddings = get_embeddings(metaphor_phrases)

    # Compute cosine similarity between corpus and known metaphor phrases
    similarity_matrix = cosine_similarity(corpus_embeddings, metaphor_embeddings)

    # Identify top matching metaphorical phrases
    top_matches = np.argmax(similarity_matrix, axis=1)

    # Create a mapping of corpus phrases to most similar metaphor phrases
    metaphor_predictions = [
        (corpus_phrases[i], metaphor_phrases[top_matches[i]], similarity_matrix[i, top_matches[i]])
        for i in range(len(corpus_phrases))
    ]

    return metaphor_predictions
