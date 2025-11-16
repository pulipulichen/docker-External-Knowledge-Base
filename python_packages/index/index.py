
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../knowledge_base_files')

def index_file(knowledge_id, section_name):

    # logger.info(f"Knowledge ID: {knowledge_id}")

    config = get_knowledge_base_config(knowledge_id)
    if config is None:
        logger.error(f"Could not retrieve config for knowledge ID: {knowledge_id}")
        return False

    filename = config.get('file_name')
    filepath = os.path.join(FILE_STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        logger.error(f"File not found at path: {filepath}")
        return False

    if filename:
        logger.info(f"Filename for knowledge ID '{knowledge_id}': {filename}")
    else:
        logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")
