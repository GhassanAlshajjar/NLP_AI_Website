from flask import Flask
from .routes import routes
import firebase_admin
from firebase_admin import credentials, initialize_app, db
import secrets
import os
import zipfile
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from .routes_debug import debug

def is_time_synced():
    try:
        utc_now = datetime.now(timezone.utc)
        local_now = datetime.now().astimezone()
        local_as_utc = local_now.astimezone(timezone.utc)

        diff = abs((utc_now - local_as_utc).total_seconds())
        print(f"🔄 UTC Time: {utc_now}")
        print(f"🕒 Local Time (converted to UTC): {local_as_utc}")
        print(f"⏱️ Time Difference: {diff} seconds")
        return diff < 300
    except Exception as e:
        print(f"⚠️ Time sync check failed: {e}")
        return True

def download_and_extract_model():
    print("🚀 Starting model download check...")

    extract_path = "/mnt/model"
    os.makedirs(extract_path, exist_ok=True)

    model_url = os.getenv("MODEL_URL")
    zip_path = os.path.join(extract_path, "model.zip")
    model_dir = os.path.join(extract_path, "training", "bert-metaphor-token-model")
    required_files = [
        "config.json", "model.safetensors", "tokenizer_config.json",
        "tokenizer.json", "vocab.txt", "special_tokens_map.json"
    ]

    # Check if model is already fully extracted
    if os.path.exists(model_dir) and all(os.path.exists(os.path.join(model_dir, f)) for f in required_files):
        print("✅ Model already exists and is complete. Skipping download.")
        return

    print(f"📥 Downloading model.zip from: {model_url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(model_url, stream=True, headers=headers, allow_redirects=True)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            f.flush()
        os.sync()

        # Check first 4 bytes to verify it's a ZIP
        with open(zip_path, "rb") as f:
            header = f.read(4)
            if header != b"PK\x03\x04":
                print("❌ Not a valid ZIP file (missing ZIP header).")
                f.seek(0)
                preview = f.read(300).decode(errors="ignore")
                print("📄 File preview:\n", preview)
                return

        if zipfile.is_zipfile(zip_path):
            print("✅ ZIP verified. Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            os.remove(zip_path)
            print("✅ Extraction complete.")
        else:
            print("❌ ZIP file verification failed.")
            return

        # Final directory check
        for root, dirs, files in os.walk(model_dir):
            print(f"📁 {root}")
            for file in files:
                print(f"   └── 📄 {file}")

    except Exception as e:
        print(f"❌ Error downloading or extracting model: {e}")

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )

    load_dotenv()
    app.secret_key = secrets.token_hex(32)

    # ✅ Download model at startup
    download_and_extract_model()

    if not is_time_synced():
        print("⚠️ WARNING: System clock might be out of sync. This could cause Firebase JWT errors.")

    # ✅ Firebase setup
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", os.path.join(base_dir, "config", "firebase_credentials.json"))

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found at: {cred_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred, {
            'databaseURL': 'https://nlp-website-29590-default-rtdb.europe-west1.firebasedatabase.app/'
        })

    # ✅ Register routes
    app.register_blueprint(routes)
    app.register_blueprint(debug)

    return app
