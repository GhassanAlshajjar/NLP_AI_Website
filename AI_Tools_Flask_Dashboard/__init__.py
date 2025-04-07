from flask import Flask
from .routes import routes
import firebase_admin
from firebase_admin import credentials, initialize_app, db
import secrets
import os
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
        return True  # Don't block app startup

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates")
    )

    app.secret_key = secrets.token_hex(32)

    # Load environment variables
    load_dotenv()

    # Optional: Warn if time is off
    if not is_time_synced():
        print("⚠️ WARNING: System clock might be out of sync. This could cause Firebase JWT errors.")

    # Initialize Firebase Admin SDK (Realtime DB only)
    cred_path = os.path.join(base_dir, "config", "firebase_credentials.json")
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
