import os
import time
import platform
from datetime import timedelta
from dotenv import load_dotenv
from AI_Tools_Flask_Dashboard import create_app
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load env vars
load_dotenv()

# Create Flask app
app = create_app()

# Secret/session config
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")
app.permanent_session_lifetime = timedelta(days=30)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
