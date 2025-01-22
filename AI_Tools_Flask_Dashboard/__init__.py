from flask import Flask
from .routes import routes
import firebase_admin
from firebase_admin import credentials
import secrets
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
 
    cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "firebase_credentials.json")
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found at: {cred_path}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://nlp-website-29590-default-rtdb.europe-west1.firebasedatabase.app/'
    })

    app.register_blueprint(routes)

    return app
