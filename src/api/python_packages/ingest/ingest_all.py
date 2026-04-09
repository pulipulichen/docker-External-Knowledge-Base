"""HTTP handler to queue ingest (index) for every knowledge base config."""

import asyncio
import logging
import os
import threading

from flask import Blueprint, jsonify, request

from ..auth.check_auth import check_auth
from .ingest import ingest_data

ingest_all_bp = Blueprint("ingest_all", __name__)

logger = logging.getLogger(__name__)

CONFIGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../..",
    "knowledge_base",
    "configs",
)


def _list_config_knowledge_ids() -> list[str]:
    if not os.path.isdir(CONFIGS_DIR):
        return []
    ids: list[str] = []
    for f in os.listdir(CONFIGS_DIR):
        if f.endswith(".yml") or f.endswith(".yaml"):
            ids.append(f.rsplit(".", 1)[0])
    ids.sort()
    return ids


def _run_ingest_all_sequential(knowledge_ids: list[str], force_update: bool) -> None:
    """Run ingest for each config in order (one event loop, one KB at a time)."""

    async def run() -> None:
        for kid in knowledge_ids:
            try:
                await ingest_data(kid, None, force_update)
            except Exception:
                logger.exception("ingest_all failed for knowledge_id=%s", kid)

    asyncio.run(run())


@ingest_all_bp.route("/ingest/all", methods=["POST"])
async def ingest_all_endpoint():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True) or {}
    force_update = data.get("force_update", True)
    if not isinstance(force_update, bool):
        return jsonify({"error": "force_update must be a JSON boolean"}), 400

    knowledge_ids = _list_config_knowledge_ids()
    if not knowledge_ids:
        return (
            jsonify(
                {
                    "error": "No knowledge base configs found",
                    "detail": f"Directory missing or empty: {CONFIGS_DIR}",
                }
            ),
            404,
        )

    thread = threading.Thread(
        target=_run_ingest_all_sequential,
        args=(knowledge_ids, force_update),
        daemon=True,
    )
    thread.start()

    return (
        jsonify(
            {
                "message": "Ingest queued for all configs",
                "knowledge_ids": knowledge_ids,
                "count": len(knowledge_ids),
                "force_update": force_update,
            }
        ),
        202,
    )
