import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify

from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

upload_file_bp = Blueprint('upload_file', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

from ..ingest.fire_and_forget_ingest import fire_and_forget_ingest
from .convert_to_ods import convert_to_ods

from ..auth.check_auth import check_auth # Import check_auth from the new auth module

@upload_file_bp.route('/upload_file', methods=['POST'])
async def upload_file_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    knowledge_id_raw = request.form.get('knowledge_id')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not knowledge_id_raw:
        return jsonify({"error": "No knowledge_id provided"}), 400

    parsed_id = parse_knowledge_id(knowledge_id_raw)
    knowledge_id = parsed_id["knowledge_id"]
    section_name = parsed_id["section_name"]

    try:
        config = get_knowledge_base_config(knowledge_id)
        
        if not config:
            return jsonify({"error": "Knowledge base configuration not found"}), 404

        # logging.debug(f"Type of config: {type(config)}")
        # logging.debug(f"Content of config: {config}")
        file_path = config.get('file_path')


        if not file_path:
            return jsonify({"error": "Path not found in knowledge base configuration"}), 400
        

        # ==============

        # 如果檔案格式是xlsx或xls，要把它轉換成ods
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension in ['.xlsx', '.xls']:
            file_path = convert_to_ods(file, file_path, file_extension)
        else:
            file.save(file_path)
        # logging.debug(f"File saved to {file_path}")

        fire_and_forget_ingest(knowledge_id, section_name, True)


        return jsonify({"message": "File uploaded successfully", "path": file_path}), 200

    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(upload_file_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
