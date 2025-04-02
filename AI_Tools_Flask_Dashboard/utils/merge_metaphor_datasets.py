# merge_metaphor_datasets.py

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
data_dir = os.path.join(BASE_DIR, "data")
output_path = os.path.join(data_dir, "combined_metaphor_dataset.csv")

datasets = [
    {"file": "MOH-X.csv", "source": "MOH-X"},
    {"file": "TroFi.csv", "source": "TroFi"},
    {"file": "VUA_metaphor.csv", "source": "VUA"},
]

merged = []

for ds in datasets:
    path = os.path.join(data_dir, ds["file"])
    if not os.path.exists(path):
        print(f"⚠️ Skipping {ds['file']} (not found)")
        continue

    encodings = ["utf-8", "ISO-8859-1", "windows-1252", "latin-1"]
    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception:
            continue

    if df is None:
        print(f"❌ Could not read {ds['file']} with any known encoding.")
        continue

    # Try to normalize column names
    sentence_col = next((col for col in df.columns if "sentence" in col.lower()), None)
    label_col = next((col for col in df.columns if "label" in col.lower()), None)

    if sentence_col is None:
        print(f"❌ {ds['file']} has no sentence column.")
        continue

    if label_col is None:
        print(f"⚠️ {ds['file']} has no label column. Assuming all are metaphors.")
        df["label"] = 1
        label_col = "label"

    df_clean = df[[sentence_col, label_col]].rename(columns={sentence_col: "sentence", label_col: "label"})
    df_clean["source"] = ds["source"]
    df_clean.dropna(subset=["sentence"], inplace=True)
    df_clean["sentence"] = df_clean["sentence"].astype(str).str.strip()

    merged.append(df_clean)

if not merged:
    print("❌ No datasets were found. Make sure they exist in the data/ folder.")
    exit(1)

# Combine and clean up
final_df = pd.concat(merged, ignore_index=True)
final_df.drop_duplicates(subset=["sentence"], inplace=True)
final_df.to_csv(output_path, index=False)

print(f"✅ Merged {len(final_df)} examples into {output_path}")
