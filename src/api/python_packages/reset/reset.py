import asyncio
import logging
import os
import shutil

from flask import Blueprint, jsonify, request

from ..auth.check_auth import check_auth
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..knowledge_base_config.parse_knowledge_id import parse_knowledge_id
from ..weaviate.weaviate_collection_delete import weaviate_collection_delete

reset_bp = Blueprint("reset", __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

FILE_STORAGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../../../", "knowledge_base/files"
)


def _safe_remove_path(path: str) -> bool:
    """Remove a file or directory tree. Returns True if something was removed."""
    if not path or not os.path.exists(path):
        return False
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True
    except OSError as e:
        logger.error("Failed to remove path %s: %s", path, e)
        return False


def remove_knowledge_artifacts(knowledge_id: str, config: dict) -> dict:
    """Remove generated markdown under `.md` and the index timestamp file under `.time`."""
    removed: dict = {
        "markdown_removed": False,
        "index_time_removed": False,
        "paths_removed": [],
    }

    index_time = config.get("index_time_filepath")
    if index_time and _safe_remove_path(index_time):
        removed["index_time_removed"] = True
        removed["paths_removed"].append(index_time)

    file_name = config.get("file_name")
    if not file_name:
        return removed

    if config.get("is_file", True):
        md_path = os.path.join(FILE_STORAGE_DIR, ".md", file_name)
        if _safe_remove_path(md_path):
            removed["markdown_removed"] = True
            removed["paths_removed"].append(md_path)
    else:
        md_dir = os.path.join(FILE_STORAGE_DIR, ".md", file_name) + "-index"
        if _safe_remove_path(md_dir):
            removed["markdown_removed"] = True
            removed["paths_removed"].append(md_dir)

    return removed


@reset_bp.route("/reset", methods=["POST"])
async def reset_endpoint():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)
    knowledge_id_raw = data.get("knowledge_id", "")
    if not knowledge_id_raw or not isinstance(knowledge_id_raw, str):
        return (
            jsonify({"error": "JSON body must include a string field 'knowledge_id'"}),
            400,
        )

    parsed = parse_knowledge_id(knowledge_id_raw.strip())
    knowledge_id = parsed["knowledge_id"]

    config = get_knowledge_base_config(knowledge_id)
    if not config or not config.get("file_name"):
        return (
            jsonify(
                {
                    "error": "Unknown knowledge_id",
                    "detail": f"No config found for '{knowledge_id}'",
                }
            ),
            404,
        )

    weaviate_result: dict | None = None
    
    try:
        delete_return = await asyncio.to_thread(
            weaviate_collection_delete, knowledge_id=knowledge_id
        )
        weaviate_result = {
            "skipped": False,
            "collection_existed": delete_return is not False,
        }
    except Exception as e:
        logger.exception("Weaviate delete failed for %s", knowledge_id)
        return (
            jsonify(
                {"error": "Weaviate delete failed", "detail": str(e)},
            ),
            502,
        )

    fs_result = await asyncio.to_thread(remove_knowledge_artifacts, knowledge_id, config)

    return (
        jsonify(
            {
                "knowledge_id": knowledge_id,
                "weaviate": weaviate_result,
                "filesystem": fs_result,
            }
        ),
        200,
    )


if __name__ == "__main__":
    from flask import Flask

    _app = Flask(__name__)
    _app.register_blueprint(reset_bp)
    _app.run(host="0.0.0.0", port=80, debug=True)
