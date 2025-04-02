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
tokenizer = BertTokenizerFast.from_pretrained(MODEL_PATH)
model = BertForTokenClassification.from_pretrained(MODEL_PATH)
model.eval()

id_to_label = {0: "O", 1: "B-MET", 2: "B-LIT"}

def enhanced_highlight_and_link(sentence, metaphor_tokens):
    doc = nlp(sentence)
    highlighted = sentence
    explanations = []
    phrases = set()

    for token in doc:
        clean_text = token.text.lower()
        if clean_text in metaphor_tokens:
            subject = ""
            obj = ""
            prep_phrase = ""

            for child in token.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subject = child.text
                elif child.dep_ in ("dobj", "attr", "pobj", "nmod"):
                    obj = child.text
                elif child.dep_ == "prep":
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            prep_phrase = f"{child.text} {grandchild.text}"

            parts = [subject, token.text, obj, prep_phrase]
            phrase = " ".join(part for part in parts if part).strip()
            phrases.add(phrase if phrase else token.text)

            if subject and token.pos_ == "VERB":
                explanation = f"The metaphor applies to '{subject}' through the verb '{token.text}', suggesting a human-like or forceful action."
            elif obj:
                explanation = f"The phrase '{token.text} {obj}' may describe a non-literal impact on '{obj}'."
            else:
                explanation = f"The word '{token.text}' is metaphorical based on its abstract or figurative context."

            explanations.append(explanation)

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
