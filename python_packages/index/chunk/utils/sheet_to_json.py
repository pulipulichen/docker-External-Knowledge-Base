from __future__ import annotations
import base64
import json
import os
import sys
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import pyexcel_ods
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

# Add python_packages to sys.path to allow importing image_describe
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the python_packages directory: python_packages/index/chunk/utils/
package_root = os.path.abspath(os.path.join(current_dir, "../../../../"))
if package_root not in sys.path:
    sys.path.append(package_root)

from image_describe.image_describe import image_describe

logger = logging.getLogger(__name__)

def _get_headers(ws: Worksheet, header_row: int = 1) -> List[str]:
    """獲取指定列作為標頭，處理空白標頭並確保唯一性。"""
    headers: List[str] = []
    for cell in ws[header_row]:
        h = str(cell.value).strip() if cell.value is not None else ""
        headers.append(h)
    return headers

def _col_index_to_header(headers: List[str], col_1based: int) -> str:
    """根據列索引返回標頭名稱，若無標頭則回傳預設名稱。"""
    idx = col_1based - 1
    if 0 <= idx < len(headers) and headers[idx]:
        return headers[idx]
    return f"COL_{col_1based}"

def _collect_images(ws: Worksheet) -> Dict[tuple[int, int], List[str]]:
    """提取工作表中的圖片並轉換為 Base64。"""
    image_data: Dict[tuple[int, int], List[str]] = {}
    for img in getattr(ws, "_images", []):
        try:
            # 獲取圖片所在的行與列 (1-based)
            row = img.anchor._from.row + 1
            col = img.anchor._from.col + 1
            
            # 讀取圖片位元組並編碼
            raw_bytes = img._data()
            b64_str = base64.b64encode(raw_bytes).decode("utf-8")
            
            image_data.setdefault((row, col), []).append(b64_str)
        except Exception:
            continue
    return image_data

def _process_ods(filepath: str, section_name: Optional[str] = None, include_fields: Optional[List[str]] = None) -> List[OrderedDict]:
    """處理 ODS 檔案。"""
    try:
        book = pyexcel_ods.get_data(filepath)
    except Exception:
        if os.path.islink(filepath):
            filepath = os.path.realpath(filepath)
        os.system(f"cat '{filepath}' > /dev/null")
        os.system(f"cp '{filepath}' /tmp")
        filepath = os.path.join('/tmp', os.path.basename(filepath))
        book = pyexcel_ods.get_data(filepath)

    if section_name is None:
        if not book:
            logger.error(f"ODS file '{filepath}' is empty or corrupted.")
            return []
        section_name = list(book.keys())[0]

    if section_name not in book:
        logger.error(f"Sheet '{section_name}' not found in the ODS file.")
        return []

    sheet_data = book[section_name]
    if not sheet_data:
        logger.warning(f"Sheet '{section_name}' is empty.")
        return []

    keys = [str(cell).strip() for cell in sheet_data[0]]
    json_array = []
    include_fields_list = include_fields if include_fields else []

    for row_index in range(1, len(sheet_data)):
        row_values = sheet_data[row_index]
        row_dict = OrderedDict()
        is_empty = True
        for i, key in enumerate(keys):
            value = row_values[i] if i < len(row_values) else ""
            cleaned_value = str(value).strip()
            if cleaned_value:
                if not include_fields_list or key in include_fields_list:
                    row_dict[key] = cleaned_value
                    is_empty = False

        if not is_empty:
            row_dict['__row_index__'] = row_index
            json_array.append(row_dict)
    return json_array

def _process_xlsx(filepath: str, section_name: Optional[str] = None, include_fields: Optional[List[str]] = None, header_row: int = 1) -> List[OrderedDict]:
    """處理 XLSX 檔案，包含圖片描述。"""
    wb = load_workbook(filepath, data_only=True)
    ws = wb[section_name] if section_name else wb.active

    headers = _get_headers(ws, header_row)
    images_map = _collect_images(ws)
    
    data_start_row = header_row + 1
    max_row = ws.max_row
    max_col = max(ws.max_column or 0, len(headers))

    result_rows = []
    include_fields_list = include_fields if include_fields else []

    for r in range(data_start_row, max_row + 1):
        row_dict = OrderedDict()
        is_empty = True

        for c in range(1, max_col + 1):
            key = _col_index_to_header(headers, c)
            if include_fields_list and key not in include_fields_list:
                continue

            val = ws.cell(row=r, column=c).value
            text_val = str(val).strip() if val is not None and val != "" else ""
            if text_val:
                is_empty = False
            
            imgs = images_map.get((r, c))
            image_descriptions = []
            if imgs:
                for img_b64 in imgs:
                    try:
                        desc = image_describe(img_b64)
                        if desc and not desc.startswith("Error:"):
                            image_descriptions.append(desc)
                    except Exception:
                        continue
                if image_descriptions:
                    is_empty = False

            final_val = None
            if text_val and image_descriptions:
                desc_text = "\n".join(image_descriptions)
                final_val = {"text": text_val, "images_description": desc_text}
            elif text_val:
                final_val = text_val
            elif image_descriptions:
                final_val = "\n".join(image_descriptions)
            
            if final_val is not None:
                row_dict[key] = final_val

        if not is_empty:
            row_dict['__row_index__'] = r - header_row
            result_rows.append(row_dict)
    return result_rows

def sheet_to_json(filepath: str, section_name: Optional[str] = None, include_fields: Optional[List[str]] = None, header_row: int = 1) -> List[OrderedDict]:
    """
    Reads a sheet file (ODS or XLSX) and converts it into a list of dictionaries.
    
    Args:
        filepath: The path to the file.
        section_name: The name of the sheet to extract.
        include_fields: List of field names to include.
        header_row: The row index (1-based) where headers are located (for XLSX).
        
    Returns:
        A list of OrderedDict objects representing the rows.
    """
    if not os.path.exists(filepath):
        logger.error(f"File '{filepath}' does not exist.")
        return []
    
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.ods':
        return _process_ods(filepath, section_name, include_fields)
    elif ext == '.xlsx':
        return _process_xlsx(filepath, section_name, include_fields, header_row)
    else:
        logger.error(f"Unsupported file extension: {ext}")
        return []

