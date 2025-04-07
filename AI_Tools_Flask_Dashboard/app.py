import os
import time
import platform
import requests
import zipfile
from datetime import timedelta
from dotenv import load_dotenv
from AI_Tools_Flask_Dashboard import create_app
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Set timezone if not Windows
if platform.system() != "Windows":
    os.environ['TZ'] = 'UTC'
    time.tzset()

# Load .env variables
load_dotenv()

def download_and_extract_model():
    model_url = os.getenv("MODEL_URL")
    target_dir = os.path.join("AI_Tools_Flask_Dashboard")
    zip_path = "model.zip"
    model_dir = os.path.join(target_dir, "training")
    os.makedirs(model_dir, exist_ok=True)

    expected_file = os.path.join(model_dir, "model.pkl")
    if os.path.exists(expected_file):
        print("✅ Model already exists. No download needed.")
        return

    print(f"📥 Downloading model.zip from: {model_url}")
    try:
        response = requests.get(model_url, stream=True)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if zipfile.is_zipfile(zip_path):
            print("✅ Download complete. Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(target_dir)  # 👈 Extract into AI_Tools_Flask_Dashboard/
            print("✅ Extraction complete.")
            os.remove(zip_path)
        else:
            print("❌ File is not a valid ZIP archive. Possibly an HTML response.")
            with open(zip_path, "r", encoding="utf-8", errors="ignore") as f:
                print("📄 File preview:\n", f.read(300))

    except Exception as e:
        print(f"❌ Error downloading or extracting model: {e}")

# Run the model downloader
download_and_extract_model()

# Create the Flask app
app = create_app()

# Secret and session config
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")
app.permanent_session_lifetime = timedelta(days=30)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Start the server
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
