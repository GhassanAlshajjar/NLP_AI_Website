import os, zipfile, gdown
from flask import Blueprint, jsonify
import requests

debug = Blueprint("debug", __name__)

@debug.route("/check-disk", methods=["GET"])
def check_disk():
    path = "/mnt/model"
    exists = os.path.exists(path)
    contents = os.listdir(path) if exists else []

    return jsonify({
        "path_exists": exists,
        "path": path,
        "contents": contents
    })

@debug.route("/upload-model", methods=["GET"])
def upload_model():
    model_url = "https://firebasestorage.googleapis.com/v0/b/nlp-website-29590.firebasestorage.app/o/Model.zip?alt=media&token=b9fc4df0-d11a-42f8-af9a-9ebce2a9de30"
    output_path = "/mnt/model/model.zip"
    extract_path = "/mnt/model"

    model_path = os.path.join(extract_path, "training", "bert-metaphor-token-model")
    if os.path.exists(model_path):
        return jsonify({"message": "✅ Model already exists. Skipping download."})

    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if zipfile.is_zipfile(output_path):
            with zipfile.ZipFile(output_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            os.remove(output_path)
            return jsonify({"message": "✅ Model downloaded and extracted."})
        else:
            return jsonify({"error": "❌ Not a valid ZIP (check content of Firebase file)."})

    except Exception as e:
        return jsonify({"error": str(e)})

