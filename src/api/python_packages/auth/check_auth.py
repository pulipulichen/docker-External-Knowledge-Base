import os
import logging
from flask import Flask, request

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

# Your API KEY (use environment variable in production)
API_KEY = os.getenv('API_KEY')

def check_auth(request):
    """Checks Authorization: Bearer xxx"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        app.logger.debug("Authorization header missing or malformed.")
        return False
    
    token = auth.split("Bearer ")[-1].strip()
    return token == API_KEY
