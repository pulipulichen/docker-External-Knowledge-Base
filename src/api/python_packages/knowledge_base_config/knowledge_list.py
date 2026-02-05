import os
from flask import Blueprint, jsonify, request
from ..auth.check_auth import check_auth

knowledge_list_bp = Blueprint('knowledge_list', __name__)

@knowledge_list_bp.route('/knowledge-ids', methods=['GET'])
def get_knowledge_ids():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    configs_dir = os.path.join(os.path.dirname(__file__), '../../../knowledge_base/configs')
    knowledge_ids = []
    
    if os.path.exists(configs_dir):
        for f in os.listdir(configs_dir):
            if f.endswith('.yml') or f.endswith('.yaml'):
                knowledge_ids.append(f.rsplit('.', 1)[0])
    
    knowledge_ids.sort()
    return jsonify(knowledge_ids)
