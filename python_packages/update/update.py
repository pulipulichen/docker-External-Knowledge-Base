import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify

from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

update_bp = Blueprint('update', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

from ..ingest.fire_and_forget_ingest import fire_and_forget_ingest

@update_bp.route('/update', methods=['POST'])
async def update_endpoint():
    
    knowledge_id_raw = request.form.get('knowledge_id')

    if not knowledge_id_raw:
        return jsonify({"error": "No knowledge_id provided"}), 400

    parsed_id = parse_knowledge_id(knowledge_id_raw)
    knowledge_id = parsed_id["knowledge_id"]
    section_name = parsed_id["section_name"]

    try:
        config = get_knowledge_base_config(knowledge_id)
        
        if not config:
            return jsonify({"error": "Knowledge base configuration not found"}), 404

        fire_and_forget_ingest(knowledge_id, section_name, True)

        return True

    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(update_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
