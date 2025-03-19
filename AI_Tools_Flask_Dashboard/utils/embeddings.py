from sentence_transformers import SentenceTransformer

# Load a pre-trained embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Function to generate embeddings
def get_embeddings(phrases):
    return embed_model.encode(phrases, convert_to_numpy=True)
