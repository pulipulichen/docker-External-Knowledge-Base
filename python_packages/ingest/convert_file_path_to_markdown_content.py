import logging
import os

from markitdown import MarkItDown
md = MarkItDown(enable_plugins=False) # Set to True to enable plugins

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def convert_file_path_to_markdown_content(file_path):
    try:
        markdown_content = md.convert(file_path)
        return markdown_content.text_content

    except Exception as e:
        logger.error(f"Error converting file for input_file_path '{file_path}': {e}")
        return False