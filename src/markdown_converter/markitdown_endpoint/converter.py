from markitdown import MarkItDown

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_md_instance = None

import os
IMAGE_DESCRIPTION_ENABLED = os.environ.get("IMAGE_DESCRIPTION_ENABLED", "false")

from .process_image_description import process_image_description

def get_markitdown():
    """Lazy-init MarkItDown in the current worker process."""
    global _md_instance
    if _md_instance is None:
        _md_instance = MarkItDown()
    return _md_instance


def convert_path_to_markdown(file_path: str) -> str:
    """Run MarkItDown on a local file path; returns extracted markdown text."""
    md = get_markitdown()
    markdown_content = md.convert(file_path, keep_data_uris=True).text_content

    if IMAGE_DESCRIPTION_ENABLED == "true":
        markdown_content = process_image_description(markdown_content)
    
    # logger.info("markdown_content: %s", markdown_content)

    return markdown_content
