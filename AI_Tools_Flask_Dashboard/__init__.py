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
    base_dir = os.path.abspath(os.path.dirname(__file__))
    zip_path = os.path.join(base_dir, "model.zip")
    extract_path = os.path.join(base_dir)
    os.makedirs(extract_path, exist_ok=True)

    model_url = os.getenv("MODEL_URL")
    expected_file = os.path.join(extract_path, "bert-metaphor-token-model", "config.json")
    if os.path.exists(expected_file):
        print("✅ Model already exists. No download needed.")
        return

    print(f"📥 Downloading model.zip from: {model_url}")
    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if zipfile.is_zipfile(zip_path):
            print("✅ Download complete. Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            print("✅ Extraction complete.")
        else:
            print("❌ Not a valid ZIP. Possibly an HTML error.")
            with open(zip_path, "r", encoding="utf-8", errors="ignore") as f:
                print("📄 File preview:\n", f.read(300))

        os.remove(zip_path)

        print("✅ Extraction complete.")
        debug_directory_structure(base_dir)

    except Exception as e:
        print(f"❌ Error downloading or extracting model: {e}")

def debug_directory_structure(base_dir):
    print("\n📂 Directory structure after extraction:")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}📄 {f}")

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )

    # Load environment variables
    load_dotenv()

    app.secret_key = secrets.token_hex(32)

    # Download model at startup
    download_and_extract_model()

    # Optional: Warn if time is off
    if not is_time_synced():
        print("⚠️ WARNING: System clock might be out of sync. This could cause Firebase JWT errors.")

    # Initialize Firebase Admin SDK (Realtime DB only)
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", os.path.join(base_dir, "config", "firebase_credentials.json"))

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found at: {cred_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred, {
            'databaseURL': 'https://nlp-website-29590-default-rtdb.europe-west1.firebasedatabase.app/'
        })

    # Register routes
    app.register_blueprint(routes)

    return app
