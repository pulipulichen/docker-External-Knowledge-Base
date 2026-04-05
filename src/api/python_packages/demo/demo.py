import os

from flask import Blueprint, render_template

demo_bp = Blueprint('demo', __name__)

from logging import getLogger

logger = getLogger(__name__)

def _configs_dir() -> str:
    # demo.py -> .../src/api/python_packages/demo; repo root is four parents up
    return os.path.resolve(
        os.path.dirname(__file__),
        '../../../../knowledge_base/configs',
    )


def list_knowledge_ids_from_configs() -> list[str]:
    configs_dir = _configs_dir()

    logger.info(f"configs_dir: {configs_dir}")

    knowledge_ids: list[str] = []
    if os.path.exists(configs_dir):
        for f in os.listdir(configs_dir):
            if f.endswith('.yml') or f.endswith('.yaml'):
                knowledge_ids.append(f.rsplit('.', 1)[0])
    knowledge_ids.sort()
    return knowledge_ids


@demo_bp.route('/demo')
def demo():
    knowledge_ids = list_knowledge_ids_from_configs()
    return render_template('demo_query.html', knowledge_ids=knowledge_ids)
