import json
import os
import logging
from flask import Blueprint, Flask, request, jsonify

from .mock_retrieval import get_mock_results
from .db_retrieval import get_db_results
from .db_retrieval_file import get_db_file_results
from ..auth.check_auth import check_auth # Import check_auth from the new auth module

from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

retrieval_bp = Blueprint('retrieval', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"


def _parse_field_list(value):
    if isinstance(value, str):
        return [field.strip() for field in value.split(",") if field.strip()]
    if isinstance(value, list):
        return [str(field).strip() for field in value if str(field).strip()]
    return []


def _get_display_fields(data, retrieval_setting, config):
    display_fields = retrieval_setting.get("display_fields", data.get("display_fields"))
    if display_fields is None:
        display_fields = config.get("display_fields", "")
    return _parse_field_list(display_fields)


def _strip_metadata_from_records(results):
    """Remove metadata from each record when disable_metadata is requested."""
    records = results.get("records")
    if not records:
        return
    for rec in records:
        if isinstance(rec, dict):
            rec.pop("metadata", None)


def _get_nested_value(record, field_path):
    current = record
    for part in field_path.split("."):
        if not isinstance(current, dict) or part not in current:
            current = None
            break
        current = current[part]
    if current is not None:
        return current

    metadata = record.get("metadata", {})
    if "." not in field_path and isinstance(metadata, dict):
        if field_path in metadata:
            return metadata.get(field_path)
        try:
            display_fields = json.loads(metadata.get("_display_fields", "{}"))
        except (TypeError, json.JSONDecodeError):
            display_fields = {}
        if isinstance(display_fields, dict):
            return display_fields.get(field_path)

    current = metadata
    for part in field_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _set_nested_value(record, field_path, value):
    current = record
    parts = field_path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _filter_records_by_fields(results, fields):
    if not fields:
        return
    records = results.get("records")
    if not records:
        return
    filtered_records = []
    for rec in records:
        if not isinstance(rec, dict):
            filtered_records.append(rec)
            continue
        filtered_record = {}
        for field in fields:
            value = _get_nested_value(rec, field)
            if value is not None:
                _set_nested_value(filtered_record, field, value)
        filtered_records.append(filtered_record)
    results["records"] = filtered_records


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
    config = get_knowledge_base_config(knowledge_id)
    # app.logger.debug(f"Parsed knowledge_id: {knowledge_id}, section_name: {section_name}")
    
    query = data.get("query", "")
    
    retrieval_setting = data.get("retrieval_setting", {})

    top_k = retrieval_setting.get("top_k", 5)
    score_threshold = retrieval_setting.get("score_threshold", None)
    disable_metadata = retrieval_setting.get("disable_metadata", data.get("disable_metadata", False))
    file_mode = retrieval_setting.get("file_mode", data.get("file_mode", False))
    display_fields = _get_display_fields(data, retrieval_setting, config)


    # ==============================
    # Decide whether to use Mock Data or real DB based on USE_MOCK_DB
    # ==============================
    if USE_MOCK_DB:
        results = get_mock_results(knowledge_id, section_name, query, top_k, score_threshold)
    elif file_mode is False or file_mode is None:
        results = await get_db_results(knowledge_id, section_name, query, top_k, score_threshold)
    else:
        try:
            results = await get_db_file_results(knowledge_id, section_name, query, top_k, score_threshold)
        except Exception as e:
            results = await get_db_results(knowledge_id, section_name, query, top_k, score_threshold)

    _filter_records_by_fields(results, display_fields)

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
