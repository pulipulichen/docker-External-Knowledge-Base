import os

from flask import Blueprint, render_template

# Blueprint serves HTML/JS that POSTs to `POST /reset` (see reset.reset_bp).
reset_demo_bp = Blueprint(
    "reset_demo",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/reset-demo/static",
)

from logging import getLogger

logger = getLogger(__name__)


def _configs_dir() -> str:
    return "/app/knowledge_base/configs/"


def list_knowledge_ids_from_configs() -> list[str]:
    configs_dir = _configs_dir()
    knowledge_ids: list[str] = []
    if os.path.exists(configs_dir):
        for f in os.listdir(configs_dir):
            if f.endswith(".yml") or f.endswith(".yaml"):
                knowledge_ids.append(f.rsplit(".", 1)[0])
    knowledge_ids.sort()
    return knowledge_ids


@reset_demo_bp.route("/demo/reset")
def reset_demo_page():
    knowledge_ids = list_knowledge_ids_from_configs()
    return render_template("reset_demo.html", knowledge_ids=knowledge_ids)
