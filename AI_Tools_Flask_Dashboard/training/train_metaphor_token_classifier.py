from transformers import BertTokenizerFast, BertForTokenClassification, TrainingArguments, Trainer, DataCollatorForTokenClassification
from datasets import load_from_disk, ClassLabel
import torch
import numpy as np
import os

# Load the preprocessed dataset
dataset = load_from_disk("../data/vua_token_dataset")

# Define label list and mappings
label_list = ["O", "B-MET", "B-LIT"]
label_to_id = {label: i for i, label in enumerate(label_list)}
id_to_label = {i: label for label, i in label_to_id.items()}

# Convert string labels to IDs
def encode_labels(example):
    example["labels"] = [label_to_id.get(label, 0) for label in example["labels"]]
    return example

dataset = dataset.map(encode_labels)

# Load tokenizer and model
tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
model = BertForTokenClassification.from_pretrained("bert-base-uncased", num_labels=len(label_list))

# Training settings
training_args = TrainingArguments(
    output_dir="./bert-metaphor-token-model",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=3e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=4,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss"
)

# Data collator for dynamic padding
data_collator = DataCollatorForTokenClassification(tokenizer)

# Compute metrics (optional)
def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=2)
    labels = p.label_ids
    mask = labels != -100
    correct = (preds == labels) & mask
    accuracy = correct.sum() / mask.sum()
    return {"accuracy": accuracy}

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# ✅ Train the model
trainer.train()

# ✅ Save model
model_path = "./bert-metaphor-token-model"
trainer.save_model(model_path)
print(f"✅ Model saved to {model_path}")
