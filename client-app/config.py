import os

SECRET_KEY = os.getenv("CLIENT_APP_SECRET_KEY", "dev-flask-secret-change-in-production")
HOST = os.getenv("CLIENT_APP_HOST", "0.0.0.0")
PORT = int(os.getenv("CLIENT_APP_PORT", "5001"))

# OAuth2 client registration (must match what seed.py puts in the DB)
CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "web-client")
CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "web-client-secret")
REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:5001/callback")
DEFAULT_SCOPE = os.getenv("OAUTH2_SCOPE", "read write")

# Auth server endpoints
AUTHORIZE_URL = os.getenv("OAUTH2_AUTHORIZE_URL", "http://localhost:5000/authorize")
TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL", "http://localhost:5000/token")
REFRESH_URL = os.getenv("OAUTH2_REFRESH_URL", "http://localhost:5000/refresh")

# Resource server
RESOURCE_SERVER_URL = os.getenv("RESOURCE_SERVER_URL", "http://localhost:5002")
