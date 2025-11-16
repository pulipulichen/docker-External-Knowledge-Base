import pyexcel_ods
from collections import OrderedDict
import json
import os

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

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
            print(f"Error: File '{filepath}' does not exist.")
            return []

        book = pyexcel_ods.get_data(filepath)
        if section_name not in book:
            print(f"Error: Sheet '{section_name}' not found in the ODS file.")
            return []

        sheet_data = book[section_name]

        if not sheet_data:
            print(f"Warning: Sheet '{section_name}' is empty.")
            return []

        # The first row contains the keys
        keys = [str(cell).strip() for cell in sheet_data[0]]
        chunks = []

        # Iterate through the rest of the rows to get values
        for row_index in range(1, len(sheet_data)):
            row_values = sheet_data[row_index]
            chunk = OrderedDict()
            for i, key in enumerate(keys):
                value = row_values[i] if i < len(row_values) else ""
                chunk[key] = str(value).strip()
            chunks.append(json.dumps(chunk, ensure_ascii=False)) # Convert chunk to JSON string here
        return chunks

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
