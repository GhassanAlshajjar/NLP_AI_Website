import os, zipfile, gdown
from flask import Blueprint, jsonify

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
    file_id = "1cV939DtFIKrvGyzb-dcI8plD40sWgWCv"
    output_path = "/mnt/model/model.zip"
    extract_path = "/mnt/model"

    model_path = os.path.join(extract_path, "training", "bert-metaphor-token-model")
    if os.path.exists(model_path):
        return jsonify({"message": "✅ Model already exists. Skipping download."})

    try:
        gdown.download(id=file_id, output=output_path, quiet=False)

        if zipfile.is_zipfile(output_path):
            with zipfile.ZipFile(output_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            os.remove(output_path)
            return jsonify({"message": "✅ Model downloaded and extracted."})
        else:
            return jsonify({"error": "❌ Not a valid ZIP."})
    except Exception as e:
        return jsonify({"error": str(e)})
