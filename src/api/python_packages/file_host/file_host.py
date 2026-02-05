import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify, send_from_directory, abort

file_host_bp = Blueprint('file_host', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

KNOWLEDGE_BASE_FILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../knowledge_base/files'))

@file_host_bp.route('/f/<path:filename>', methods=['GET'])
def file_host_endpoint(filename):
    # 我要它根據後面的路徑來取得knowledge_base_files裡面對應的檔案

    # 例如 http://192.168.89.6:8080/f/prefer_terms.ods
    # http://192.168.89.6:8080/f/example_document/HTML Examples (12_27_2025 9：12：38 PM).html
    # 應該要取得 knowledge_base_files/prefer_terms.ods 給人下載
    # 如果是 html 就直接顯示
    # 檔案開頭是 . 的就不要給人下載

    # 1. 檢查檔案開頭是否為 .
    if filename.startswith('.') or '/.' in filename:
        return abort(403, description="Access to hidden files is not allowed.")

    # 2. 確保檔案存在於 knowledge_base_files 目錄中
    # send_from_directory 會處理路徑安全問題，防止目錄遍歷攻擊
    
    as_attachment = not filename.lower().endswith('.html')
    
    return send_from_directory(
        KNOWLEDGE_BASE_FILES_DIR, 
        filename, 
        as_attachment=as_attachment
    )

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(file_host_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
