import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify

from ..auth.check_auth import check_auth # Import check_auth from the new auth module

scrape_bp = Blueprint('scrape', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"

@scrape_bp.route('/scrape', methods=['POST'])
async def scrape_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Read JSON body
    data = request.get_json(force=True)

    # 這邊要接 mercury-parser 來做取得網頁的主要內容

    return results

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(scrape_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
