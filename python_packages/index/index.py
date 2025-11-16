
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

def index_file(knowledge_id):

    logger.info(f"Knowledge ID: {knowledge_id}")

    config = get_knowledge_base_config(knowledge_id)
    if config is None:
        logger.error(f"Could not retrieve config for knowledge ID: {knowledge_id}")
        return

    filename = config.get('file_name')
    if filename:
        logger.info(f"Filename for knowledge ID '{knowledge_id}': {filename}")
    else:
        logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")
