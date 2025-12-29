import pyexcel_ods
from collections import OrderedDict
import json
import os
import logging
import shutil

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)

def get_chunks_from_sheet(knowledge_id: str, section_name: str) -> list[str]:
    """
    Reads an ODS file, extracts data from a specified sheet, and returns it as a list of key-value chunks.
    The first row of the sheet is used as keys for the chunks.

    Args:
        filepath (str): The path to the ODS file.
        section_name (str): The name of the sheet to extract data from.

    Returns:
        list[str]: A list of JSON strings, where each string represents a row (chunk)
                   with keys from the first row of the sheet.
    """
    try:
        config = get_knowledge_base_config(knowledge_id)
        filepath = config.get('file_path')

        if not os.path.exists(filepath):
            logger.error(f"File '{filepath}' does not exist.")
            return []
        
        
        try:
            book = pyexcel_ods.get_data(filepath)
        except Exception as e:
            # 如果 filepath 是連接檔，那就取得原始檔案路徑後再來輸入
            if os.path.islink(filepath):
                # Resolve symlink to actual file path
                filepath = os.path.realpath(filepath)

            # logger.info(f"islink: {filepath}")
            os.system(f"cat '{filepath}' > /dev/null")
            os.system(f"cp '{filepath}' /tmp")
            filepath = os.path.join('/tmp', os.path.basename(filepath))
            # logger.info(f"tmp: {filepath}")

            book = pyexcel_ods.get_data(filepath)

        
        if section_name is None:
            if not book:
                logger.error(f"ODS file '{filepath}' is empty or corrupted.")
                return []
            section_name = list(book.keys())[0] # Use the first sheet if section_name is None
            # logger.info(f"No section_name provided, using the first sheet: '{section_name}'.")

        if section_name not in book:
            logger.error(f"Sheet '{section_name}' not found in the ODS file.")
            return []

        sheet_data = book[section_name]

        if not sheet_data:
            logger.warning(f"Sheet '{section_name}' is empty.")
            return []

        # The first row contains the keys
        keys = [str(cell).strip() for cell in sheet_data[0]]
        chunks = []

        include_fileds = config.get('include_fileds', [])

        # Iterate through the rest of the rows to get values
        for row_index in range(1, len(sheet_data)):
            row_values = sheet_data[row_index]
            chunk = OrderedDict()
            is_empty = True
            for i, key in enumerate(keys):
                value = row_values[i] if i < len(row_values) else ""
                cleaned_value = str(value).strip()
                if len(cleaned_value) > 0:
                    if len(include_fileds) == 0 or key in include_fileds:
                        chunk[key] = cleaned_value
                        is_empty = False

            if is_empty is False:
                chunks.append({
                    "chunk_id": f"{knowledge_id}_{section_name}_{row_index}",
                    "document": json.dumps(chunk, ensure_ascii=False),
                    # "metadata": {
                    #     "_item_id": filepath,
                    # }
                }) # Convert chunk to JSON string here
        return chunks

    except FileNotFoundError:
        logger.error(f"File not found at {filepath}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
