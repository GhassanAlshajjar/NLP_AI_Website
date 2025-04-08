import os, zipfile, requests
from flask import Blueprint, jsonify

debug = Blueprint("debug", __name__)

@debug.route("/check-disk", methods=["GET"])
def check_disk():
    path = "/mnt/model"
    exists = os.path.exists(path)
    contents = os.listdir(path) if exists else []

    # Walk full structure
    structure = []
    for root, dirs, files in os.walk(path):
        structure.append({
            "path": root,
            "dirs": dirs,
            "files": files
        })

    return jsonify({
        "path_exists": exists,
        "path": path,
        "contents": contents,
        "structure": structure
    })

@debug.route("/upload-model", methods=["GET"])
def upload_model():
    model_url = "https://firebasestorage.googleapis.com/v0/b/nlp-website-29590.firebasestorage.app/o/Model.zip?alt=media&token=b9fc4df0-d11a-42f8-af9a-9ebce2a9de30"
    output_path = "/mnt/model/model.zip"
    extract_path = "/mnt/model"
    model_path = os.path.join(extract_path, "training", "bert-metaphor-token-model")

    logs = []

    if os.path.exists(model_path):
        logs.append("✅ Model already exists. Skipping download.")
        return jsonify({"message": "✅ Model already exists.", "logs": logs})

    try:
        logs.append("📥 Starting download from Firebase Storage...")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(model_url, stream=True, headers=headers, allow_redirects=True)
        logs.append(f"📄 Response Code: {response.status_code}")
        logs.append(f"📄 Content-Type: {response.headers.get('Content-Type')}")

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with open(output_path, "rb") as f:
            header = f.read(4)
            logs.append(f"🧪 First 4 bytes: {header}")
            if header != b"PK\x03\x04":
                f.seek(0)
                preview = f.read(300).decode(errors="ignore")
                return jsonify({
                    "error": "❌ Not a valid ZIP (missing PK header)",
                    "preview": preview,
                    "logs": logs
                })

        if zipfile.is_zipfile(output_path):
            logs.append("✅ ZIP verified. Extracting...")
            with zipfile.ZipFile(output_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            os.remove(output_path)
            logs.append("✅ Extraction complete.")
        else:
            return jsonify({
                "error": "❌ ZIP verification failed.",
                "logs": logs
            })

        return jsonify({
            "message": "✅ Model downloaded and extracted successfully.",
            "logs": logs
        })

    except Exception as e:
        logs.append(f"❌ Exception: {str(e)}")
        return jsonify({"error": str(e), "logs": logs})
