import os
import logging
import pyexcel
import pyexcel_ods # This import is necessary for pyexcel to handle ODS files

logging.basicConfig(level=logging.DEBUG)

def convert_to_ods(file_storage, original_file_path: str, file_extension: str):
    """
    Converts an uploaded .xlsx or .xls file to .ods format.

    Args:
        file_storage: The FileStorage object from Flask's request.files.
        original_file_path (str): The intended base path for the saved file (without extension).
        file_extension (str): The original extension of the uploaded file (e.g., '.xlsx').

    Returns:
        str: The path to the converted .ods file.
    """
    temp_xlsx_path = original_file_path + ".temp" + file_extension
    file_storage.save(temp_xlsx_path)

    
    book = pyexcel.get_book(file_name=temp_xlsx_path)

    ods_file_path = os.path.splitext(original_file_path)[0] + ".ods"
    book.save_as(ods_file_path)
    
    os.remove(temp_xlsx_path)
    
    return ods_file_path
