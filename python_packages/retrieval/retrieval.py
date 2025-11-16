import os
import logging
from flask import Blueprint, Flask, request, jsonify
from python_packages.retrieval.mock_retrieval import get_mock_results
from python_packages.retrieval.db_retrieval import get_db_results

retrieval_bp = Blueprint('retrieval', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

# 你自己的 API KEY（正式環境請改成環境變數）
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"
API_KEY = os.getenv('API_KEY')

def check_auth(request):
    """檢查 Authorization: Bearer xxx"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        app.logger.debug("Authorization header missing or malformed.")
        return False
    
    token = auth.split("Bearer ")[-1].strip()
    return token == API_KEY

@retrieval_bp.route('/retrieval', methods=['POST'])
def retrieval_endpoint():
    # 驗證 Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # 讀取 JSON body
    data = request.get_json(force=True)

    query = data.get("query", "")
    top_k = data.get("top_k", 5)

    # ==============================
    # 根據 USE_MOCK_DB 決定使用 Mock Data 或真實 DB
    # ==============================
    if USE_MOCK_DB:
        results = get_mock_results(query, top_k)
    else:
        results = get_db_results(query, top_k)

    return jsonify(results)

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(retrieval_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
