import spacy

# Load English NLP model
nlp = spacy.load("en_core_web_sm")

# Function to extract noun & verb phrases
def extract_phrases(text):
    doc = nlp(text)
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    verb_phrases = [token.lemma_ for token in doc if token.pos_ in {"VERB", "ADJ"}]
    return noun_phrases, verb_phrases
