import json
import logging

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from .utils.sheet_to_json import sheet_to_json

logger = logging.getLogger(__name__)

def get_chunks_from_sheet(knowledge_id: str, section_name: str) -> list[dict]:
    """
    Reads an ODS file, extracts data from a specified sheet, and returns it as a list of key-value chunks.
    The first row of the sheet is used as keys for the chunks.

    Args:
        knowledge_id (str): The ID of the knowledge base.
        section_name (str): The name of the sheet to extract data from.

    Returns:
        list[dict]: A list of dictionaries, where each dict represents a row (chunk)
                    with keys from the first row of the sheet.
    """
    try:
        config = get_knowledge_base_config(knowledge_id)
        filepath = config.get('file_path')
        include_fields = config.get('include_fileds', [])

        json_array = sheet_to_json(filepath, section_name, include_fields)
        
        chunks = []
        for item in json_array:
            row_index = item.pop('__row_index__', 0)
            chunks.append({
                "chunk_id": f"{knowledge_id}_{section_name}_{row_index}",
                "document": json.dumps(item, ensure_ascii=False),
            })
        return chunks

    except Exception as e:
        logger.error(f"An error occurred in get_chunks_from_sheet: {e}")
        return []

