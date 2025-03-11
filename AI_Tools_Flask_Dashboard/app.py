import sys
import os
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv 
from AI_Tools_Flask_Dashboard import create_app

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

app = create_app()

app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key") 
app.permanent_session_lifetime = timedelta(days=30)

if __name__ == "__main__":
    app.run(debug=True)
