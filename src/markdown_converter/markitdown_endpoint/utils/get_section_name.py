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
    with zipfile.ZipFile(filepath, "r") as zf:
        with zf.open("xl/workbook.xml") as wb_xml:
            root = ET.parse(wb_xml).getroot()
    # Default namespace on workbook root
    for sheet in root.findall(f"{{{_XLSX_MAIN_NS}}}sheets/{{{_XLSX_MAIN_NS}}}sheet"):
        name = sheet.get("name")
        if name is not None:
            return name
    return None


def get_section_name(filepath):
    
    if filepath is None or not os.path.exists(filepath) or os.path.isdir(filepath):
        # logger.error(f"File '{filepath}' does not exist.")
        return None
    
    if filepath.endswith('.md'):
        return None

    if filepath.endswith('.xlsx'):
        try:
            first = _first_sheet_name_from_xlsx(filepath)
            return first if first is not None else None
        except Exception as e:
            logger.error(f"Error reading XLSX file '{filepath}': {e}")
            return None

    try:
        book = pyexcel_ods.get_data(filepath)
    except Exception as e:
        logger.error(f"Error reading ODS file '{filepath}': {e}")
        return None

    if not book:
        # logger.error(f"Sheet file '{filepath}' is empty or corrupted.")
        return None
    
    section_name = list(book.keys())[0] # Use the first sheet if section_name is None
    # logger.info(f"No section_name provided, using the first sheet: '{section_name}'.")

    return section_name
