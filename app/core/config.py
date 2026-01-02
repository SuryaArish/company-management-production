"""Configuration management"""
import os
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def get_firebase_config():
    """Get Firebase configuration"""
    return {
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "api_key": os.getenv("FIREBASE_API_KEY")
    }