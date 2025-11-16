import os
import logging
import pyexcel_ods
from .get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)

def get_section_name(knowledge_id):
    config = get_knowledge_base_config(knowledge_id)
    filepath = config.get('file_path')

    if not os.path.exists(filepath):
        logger.error(f"File '{filepath}' does not exist.")
        return []
    
    if filepath.endswith('.md'):
        return knowledge_id

    book = pyexcel_ods.get_data(filepath)

    if not book:
        logger.error(f"ODS file '{filepath}' is empty or corrupted.")
        return []
    section_name = list(book.keys())[0] # Use the first sheet if section_name is None
    # logger.info(f"No section_name provided, using the first sheet: '{section_name}'.")

    return section_name
