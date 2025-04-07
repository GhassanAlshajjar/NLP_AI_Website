from transformers import BertTokenizerFast
import pandas as pd
from datasets import Dataset, DatasetDict

# Load tokenizer
tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

# Load VUA dataset
vua_path = "../data/VUA_metaphor.csv"
df = pd.read_csv(vua_path, encoding='ISO-8859-1')

# Normalize text and group by sentence
grouped = df.groupby(["text_idx", "sentence_idx", "sentence"])

processed_data = []

for (text_idx, sent_idx, sentence), group in grouped:
    tokens = tokenizer.tokenize(sentence)
    token_ids = tokenizer.encode(sentence, truncation=True, padding="max_length", max_length=128)
    encoding = tokenizer(sentence, return_offsets_mapping=True, truncation=True, padding="max_length", max_length=128)
    offsets = encoding['offset_mapping']
    
    # Prepare label array
    labels = ["O"] * len(encoding["input_ids"])
    
    for _, row in group.iterrows():
        verb_idx = int(row["verb_idx"])
        is_metaphor = int(row["label"]) == 1
        
        # Tokenize sentence using spaCy or whitespace split
        words = sentence.split()
        if 0 <= verb_idx < len(words):
            verb = words[verb_idx]
            verb_start_char = sentence.find(verb)
            verb_end_char = verb_start_char + len(verb)

            # Label the tokens matching the verb span
            for i, (start, end) in enumerate(offsets):
                if start is None or end is None:
                    continue
                if start >= verb_start_char and end <= verb_end_char:
                    labels[i] = "B-MET" if is_metaphor else "B-LIT"

    processed_data.append({
        "tokens": tokenizer.convert_ids_to_tokens(encoding["input_ids"]),
        "input_ids": encoding["input_ids"],
        "attention_mask": encoding["attention_mask"],
        "labels": labels,
        "sentence": sentence
    })

# Convert to Dataset
dataset = Dataset.from_list(processed_data)
dataset = dataset.train_test_split(test_size=0.1, seed=42)

# Show preview
dataset["train"].to_pandas().head(3)

# Save dataset to disk
output_path = "../data/vua_token_dataset"
dataset_dict = DatasetDict(dataset)
dataset_dict.save_to_disk(output_path)
print(f"✅ Preprocessed dataset saved to: {output_path}")
