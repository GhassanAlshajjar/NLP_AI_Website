import os
import re
import nltk
import torch
import spacy
import pandas as pd
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer, util

# Load models
nltk.download('punkt')
nltk.download('stopwords')

nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words("english"))
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def clean_text(text):
    """Lowercase, remove punctuation and stopwords."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s]', '', text)
    words = [w for w in text.split() if w not in stop_words]
    return " ".join(words)

def extract_sentences(text):
    """Extract sentences and structure them in context groups."""
    sentences = nltk.sent_tokenize(text)
    paragraphs = []
    current_paragraph = []
    
    for sent in sentences:
        current_paragraph.append(sent)
        if len(current_paragraph) >= 3:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []
    
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))
    
    return sentences, paragraphs

def load_csv_data(file_path):
    """Load CSV files with multiple encoding attempts."""
    encodings = ["utf-8", "ISO-8859-1", "windows-1252", "latin-1"]
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc, on_bad_lines='skip')
        except Exception:
            continue
    raise ValueError(f"Could not decode {file_path}.")

def load_metaphor_corpus(dataset_paths):
    """Load labeled metaphors only."""
    metaphor_examples = {}
    for path in dataset_paths:
        if os.path.exists(path):
            df = load_csv_data(path)

            if 'label' in df.columns and 'sentence' in df.columns:
                for _, row in df[df['label'] == 1].iterrows():
                    sentence = clean_text(str(row['sentence']))
                    if sentence:
                        metaphor_examples[sentence] = row['sentence']  # Keep original for context
            
            elif 'sentence' in df.columns:
                for s in df['sentence'].dropna().tolist():
                    cleaned = clean_text(str(s))
                    if cleaned:
                        metaphor_examples[cleaned] = s

    return metaphor_examples

def train_metaphor_model(metaphor_sentences):
    """Train the metaphor model by encoding known metaphors."""
    return embedder.encode(list(metaphor_sentences.keys()), convert_to_tensor=True)

def extract_metaphor_phrase(sentence):
    """Identify key metaphorical phrases in a sentence using SpaCy."""
    doc = nlp(sentence)
    metaphors = []
    
    for token in doc:
        if token.pos_ in ["VERB", "NOUN"] and token.dep_ in ["nsubj", "dobj", "pobj"]:
            metaphors.append(token.text)
    
    return " ".join(metaphors) if metaphors else sentence

def generate_explanation(metaphor_sentence, matched_sentence):
    """Generate an explanation using syntactic similarity."""
    phrase = extract_metaphor_phrase(metaphor_sentence)
    return f"The phrase '{phrase}' is used metaphorically, similar to '{matched_sentence}'."

def detect_metaphors(text, metaphor_embeddings, metaphor_sentences, threshold=0.75):
    """Detect metaphors and provide explanations."""
    raw_sentences, paragraphs = extract_sentences(text)
    clean_sentences = [clean_text(s) for s in raw_sentences]
    
    results = []

    for i, (cleaned, raw) in enumerate(zip(clean_sentences, raw_sentences)):
        if not cleaned:
            continue

        embedding = embedder.encode([cleaned], convert_to_tensor=True)
        sim_scores = util.pytorch_cos_sim(embedding, metaphor_embeddings)
        max_score, best_idx = torch.max(sim_scores, dim=1)
        score = max_score.item()

        if score >= threshold:
            # Select best-matching metaphor sentence for context
            best_match = list(metaphor_sentences.keys())[best_idx.item()]
            full_context = metaphor_sentences[best_match]  # Get original sentence

            # Generate explanation
            explanation = generate_explanation(raw, full_context)

            results.append({
                "sentence": raw,
                "metaphorical_context": full_context,  # Use real metaphor as context
                "explanation": explanation,
                "similarity_score": round(score, 2),
                "confidence_score": f"{round(score * 100, 1)}%",
                "type": "Metaphor",
                "detected_as": "Likely Metaphor",
                "highlight": best_match
            })
    
    return results
