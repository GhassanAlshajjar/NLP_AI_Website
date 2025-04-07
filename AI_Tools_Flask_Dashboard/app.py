import os
import requests
import zipfile
from datetime import timedelta
from dotenv import load_dotenv 
from AI_Tools_Flask_Dashboard import create_app
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

def download_and_extract_model():
    model_dir = "training"
    zip_path = "model.zip"
    os.makedirs(model_dir, exist_ok=True)

    # Check if model file already exists (adjust this check as needed)
    expected_file = os.path.join(model_dir, "model.pkl")
    if not os.path.exists(expected_file):
        print("📥 Downloading model.zip from Google Drive...")
        url = os.getenv("MODEL_URL")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print("✅ Download complete. Extracting...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(model_dir)

            print("✅ Extraction complete.")
            os.remove(zip_path)

        except Exception as e:
            print(f"❌ Error downloading or extracting model: {e}")
    else:
        print("✅ Model already exists. No download needed.")

download_and_extract_model()
app = create_app()

app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key") 
app.permanent_session_lifetime = timedelta(days=30)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

if __name__ == "__main__":
    app.run(debug=True)
