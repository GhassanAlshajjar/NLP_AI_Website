# utils/metaphor_analysis.py (updated with capped results and better phrase highlighting)

import os
import torch
import nltk
import spacy
from transformers import BertTokenizer, BertForSequenceClassification
from nltk.tokenize import sent_tokenize

nltk.download("punkt")
nlp = spacy.load("en_core_web_sm")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "training", "bert-metaphor-model")

# Load tokenizer and model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
model.eval()

def extract_sentences(text):
    return sent_tokenize(text)

def highlight_phrase(sentence):
    doc = nlp(sentence)
    highlighted = []
    for token in doc:
        if token.pos_ in ["VERB", "NOUN"] and token.dep_ in ["nsubj", "dobj", "ROOT"]:
            highlighted.append(token.text)
    return list(dict.fromkeys(highlighted))[:3]

def detect_metaphors(text, threshold=0.6, limit=30):
    seen_sentences = set()
    results = []
    sentences = extract_sentences(text)

    for sentence in sentences:
        clean = sentence.strip()
        if not clean or clean in seen_sentences:
            continue
        seen_sentences.add(clean)

        inputs = tokenizer(clean, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            score = probs[0][1].item()

        if score >= threshold:
            phrase = highlight_phrase(clean)
            phrase_text = ", ".join(phrase)
            explanation = f"The phrase '{phrase_text}' in this sentence may be metaphorical based on its context."

            results.append({
                "sentence": clean,
                "phrase": phrase_text,
                "confidence_score": f"{round(score * 100, 1)}%",
                "type": "Metaphor",
                "explanation": explanation
            })

        if len(results) >= limit:
            break

    return results
