import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify

from .mock_retrieval import get_mock_results
from .db_retrieval import get_db_results
from .db_retrieval_file import get_db_file_results
from ..auth.check_auth import check_auth # Import check_auth from the new auth module

from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id

retrieval_bp = Blueprint('retrieval', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"


def _strip_metadata_from_records(results):
    """Remove metadata from each record when disable_metadata is requested."""
    records = results.get("records")
    if not records:
        return
    for rec in records:
        if isinstance(rec, dict):
            rec.pop("metadata", None)


@retrieval_bp.route('/retrieval', methods=['POST'])
async def retrieval_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Read JSON body
    data = request.get_json(force=True)

    # app.logger.debug(f"Received data: {json.dumps(data, indent=2)}")

    knowledge_id_raw = data.get("knowledge_id", "")
    file_mode = data.get("file_mode", False)
    parsed_id = parse_knowledge_id(knowledge_id_raw)
    knowledge_id = parsed_id["knowledge_id"]
    section_name = parsed_id["section_name"]
    # app.logger.debug(f"Parsed knowledge_id: {knowledge_id}, section_name: {section_name}")
    
    query = data.get("query", "")
    disable_metadata = data.get("disable_metadata", False)
    retrieval_setting = data.get("retrieval_setting", {})
    
    top_k = retrieval_setting.get("top_k", 5)
    score_threshold = retrieval_setting.get("score_threshold", None)


    # ==============================
    # Decide whether to use Mock Data or real DB based on USE_MOCK_DB
    # ==============================
    if USE_MOCK_DB:
        results = get_mock_results(knowledge_id, section_name, query, top_k, score_threshold)
    elif file_mode is False or file_mode is None:
        results = await get_db_results(knowledge_id, section_name, query, top_k, score_threshold)
    else:
        results = await get_db_file_results(knowledge_id, section_name, query, top_k, score_threshold)

    if disable_metadata:
        _strip_metadata_from_records(results)

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
