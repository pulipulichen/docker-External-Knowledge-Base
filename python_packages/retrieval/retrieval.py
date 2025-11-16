import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify


from .mock_retrieval import get_mock_results
from .db_retrieval import get_db_results

from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id

retrieval_bp = Blueprint('retrieval', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

# Your API KEY (use environment variable in production)
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"
API_KEY = os.getenv('API_KEY')

def check_auth(request):
    """Checks Authorization: Bearer xxx"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        app.logger.debug("Authorization header missing or malformed.")
        return False
    
    token = auth.split("Bearer ")[-1].strip()
    return token == API_KEY

@retrieval_bp.route('/retrieval', methods=['POST'])
async def retrieval_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Read JSON body
    data = request.get_json(force=True)

    # app.logger.debug(f"Received data: {json.dumps(data, indent=2)}")

    knowledge_id_raw = data.get("knowledge_id", "")
    parsed_id = parse_knowledge_id(knowledge_id_raw)
    knowledge_id = parsed_id["knowledge_id"]
    section_name = parsed_id["section_name"]
    app.logger.debug(f"Parsed knowledge_id: {knowledge_id}, section_name: {section_name}")
    
    query = data.get("query", "")
    retrieval_setting = data.get("retrieval_setting", {})
    
    top_k = retrieval_setting.get("top_k", 5)
    score_threshold = retrieval_setting.get("score_threshold", None)


    # ==============================
    # Decide whether to use Mock Data or real DB based on USE_MOCK_DB
    # ==============================
    if USE_MOCK_DB:
        results = get_mock_results(knowledge_id, section_name, query, top_k, score_threshold)
    else:
        results = await get_db_results(knowledge_id, section_name, query, top_k, score_threshold)

    # results_json = jsonify({
    #     "records": results
    # })

    # Display results_json in Log
    # app.logger.debug(f"Retrieval results: {results_json.get_data(as_text=True)}")

    return results

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(retrieval_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
