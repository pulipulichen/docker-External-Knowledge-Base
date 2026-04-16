import os
import logging
import zipfile
import xml.etree.ElementTree as ET

import pyexcel_ods
from .get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)

# OOXML workbook namespace (sheet names live in xl/workbook.xml; no need for full openpyxl parse).
_XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def _first_sheet_name_from_xlsx(filepath: str) -> str | None:
    """Return the first worksheet name by reading only xl/workbook.xml inside the ZIP."""

    file_path = filepath
    if os.path.islink(file_path):
        # Resolve symlink to actual file path
        file_path = os.path.realpath(file_path)

    # os.system(f"cat '{file_path}' > /dev/null")
    os.system(f"cp -f '{file_path}' /tmp")
    filepath = os.path.join('/tmp', os.path.basename(file_path))

    logger.info(f"Reading XLSX file '{filepath}' in _first_sheet_name_from_xlsx")
    with zipfile.ZipFile(filepath, "r") as zf:
        logger.info(f"get ZipFile")
        with zf.open("xl/workbook.xml") as wb_xml:
            root = ET.parse(wb_xml).getroot()
            logger.info(f"get Root")
    # Default namespace on workbook root
    for sheet in root.findall(f"{{{_XLSX_MAIN_NS}}}sheets/{{{_XLSX_MAIN_NS}}}sheet"):
        name = sheet.get("name")
        logger.info(f"Sheet name: '{name}'")
        if name is not None:
            return name
    return None


def get_section_name(knowledge_id):
    config = get_knowledge_base_config(knowledge_id)
    filepath = config.get('file_path')

    if filepath is None or not os.path.exists(filepath) or os.path.isdir(filepath):
        # logger.error(f"File '{filepath}' does not exist.")
        return knowledge_id
    
    if filepath.endswith('.md'):
        return knowledge_id

    if filepath.endswith('.xlsx'):
        try:
            logger.info(f"Reading XLSX file '{filepath}'")
            first = _first_sheet_name_from_xlsx(filepath)
            return first if first is not None else knowledge_id
        except Exception as e:
            logger.error(f"Error reading XLSX file '{filepath}': {e}")
            return knowledge_id

    try:
        book = pyexcel_ods.get_data(filepath)
    except Exception as e:
        logger.error(f"Error reading ODS file '{filepath}': {e}")
        return knowledge_id

    if not book:
        # logger.error(f"Sheet file '{filepath}' is empty or corrupted.")
        return knowledge_id
    
    section_name = list(book.keys())[0] # Use the first sheet if section_name is None
    # logger.info(f"No section_name provided, using the first sheet: '{section_name}'.")

    return section_name
