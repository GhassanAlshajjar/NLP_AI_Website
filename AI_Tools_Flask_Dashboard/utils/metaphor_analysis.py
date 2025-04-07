import os
import torch
import nltk
import spacy
from transformers import BertTokenizerFast, BertForTokenClassification
from nltk.tokenize import sent_tokenize

nltk.download("punkt")
nlp = spacy.load("en_core_web_sm")

# Load model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "training", "bert-metaphor-token-model")
tokenizer = BertTokenizerFast.from_pretrained(MODEL_PATH, local_files_only=True)
model = BertForTokenClassification.from_pretrained(MODEL_PATH, local_files_only=True)
model.eval()

id_to_label = {0: "O", 1: "B-MET", 2: "B-LIT"}

def enhanced_highlight_and_link(sentence, metaphor_tokens):
    doc = nlp(sentence)
    highlighted = sentence
    explanations = []
    phrases = set()

    for token in doc:
        if token.text.lower() in metaphor_tokens:
            # Trace full verb phrase: subject + verb + object/preposition
            subject = ""
            objects = []
            prep_phrases = []

            # Look upward to find better subject (sometimes subject is the grandparent)
            if token.head.dep_ in ("ROOT", "conj", "relcl"):
                subject = next((child.text for child in token.head.children if child.dep_ in ("nsubj", "nsubjpass")), "")

            # Objects and prepositions
            for child in token.children:
                if child.dep_ in ("dobj", "pobj", "attr", "acomp", "oprd"):
                    objects.append(child.text)
                elif child.dep_ == "prep":
                    prep = " ".join([child.text] + [gc.text for gc in child.children])
                    prep_phrases.append(prep)

            full_phrase = " ".join([subject, token.text] + objects + prep_phrases).strip()
            phrases.add(full_phrase if full_phrase else token.text)

            # Explanation logic
            if subject and token.pos_ == "VERB":
                explanations.append(f"The metaphor applies to '{subject}' through the verb '{token.text}', suggesting a human-like or forceful action.")
            elif objects:
                explanations.append(f"The phrase '{token.text} {objects[0]}' may describe a non-literal impact on '{objects[0]}'.")
            elif prep_phrases:
                explanations.append(f"The phrase '{token.text} {prep_phrases[0]}' is metaphorical based on its figurative context.")
            else:
                explanations.append(f"The word '{token.text}' is metaphorical based on its abstract or figurative context.")

    for phrase in sorted(phrases, key=len, reverse=True):
        highlighted = highlighted.replace(phrase, f"<span style='color: red;'>{phrase}</span>")

    return list(phrases), highlighted, explanations


def detect_metaphor_spans(text, start=0, per_page=25):
    results = []
    sentences = sent_tokenize(text)
    selected = sentences[start:start+per_page]

    for sentence in selected:
        inputs = tokenizer(sentence, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=2).squeeze().tolist()
        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"].squeeze())
        labels = [id_to_label.get(p, "O") for p in predictions]

        filtered = [(tokens[i], labels[i]) for i in range(len(tokens)) if tokens[i] not in tokenizer.all_special_tokens]
        metaphor_words = [tok.replace("##", "") for tok, lab in filtered if lab == "B-MET"]

        if not metaphor_words:
            continue

        spans, highlighted_sentence, explanation = enhanced_highlight_and_link(sentence, metaphor_words)

        results.append({
            "highlighted": highlighted_sentence,
            "metaphor_spans": spans,
            "explanation": explanation
        })

    return results, len(sentences)
