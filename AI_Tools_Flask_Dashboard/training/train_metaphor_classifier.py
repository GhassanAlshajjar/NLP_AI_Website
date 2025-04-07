# train_metaphor_classifier.py

import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
import torch
import os

# Check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Using device: {device}")

# Load and prepare data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "combined_metaphor_dataset.csv")

df = pd.read_csv(DATA_PATH)

df = df[["sentence", "label"]].dropna()
df["sentence"] = df["sentence"].astype(str).str.strip()
df["label"] = df["label"].astype(int)

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["sentence"].tolist(), df["label"].tolist(), test_size=0.1, random_state=42
)

train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
val_dataset = Dataset.from_dict({"text": val_texts, "label": val_labels})

# Tokenization
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

# Model
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2).to(device)

# Training config
training_args = TrainingArguments(
    output_dir="bert-metaphor-model",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=4,
    load_best_model_at_end=True,
    save_total_limit=1,
    logging_dir="./logs",
)


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

trainer.train()

# Save
model.save_pretrained("bert-metaphor-model")
tokenizer.save_pretrained("bert-metaphor-model")
print("✅ Model saved to 'bert-metaphor-model'")
