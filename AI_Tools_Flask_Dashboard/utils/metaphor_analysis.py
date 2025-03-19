import spacy

nlp = spacy.load("en_core_web_sm")

def detect_metaphors(text):
    doc = nlp(text)
    metaphors = []

    for token in doc:
        if token.pos_ in {"NOUN", "VERB"} and token.dep_ in {"amod", "nsubj"}:
            if token.head.pos_ == "ADJ":
                metaphors.append({
                    "phrase": f"{token.text} - {token.head.text}",
                    "context": " ".join([t.text for t in token.head.sent]),
                    "type": "Potential Metaphor"  # Placeholder logic
                })

    return metaphors
