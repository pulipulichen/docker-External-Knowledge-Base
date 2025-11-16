import os
import logging
from typing import List, Dict, Any

from ..weaviate.helper.segment_text import segment_text

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_chunks_from_file(filepath: str, section_name: str) -> List[Dict[str, Any]]:
    """
    Reads a file, processes its content, and splits it into chunks.

    :param filepath: The path to the file.
    :param section_name: The name of the section (its usage will be defined later).
    :return: A list of dictionaries, where each dictionary represents a chunk.
    """
    chunks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Process the content using segment_text
        processed_content = segment_text(content)

        # Simple chunking strategy: split by paragraphs (double newline)
        # For more advanced chunking, a dedicated text splitter library might be used.
        paragraphs = processed_content.split('\n\n')

        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip(): # Only add non-empty paragraphs
                chunk = {
                    "content": paragraph.strip(),
                    "metadata": {
                        "filepath": filepath,
                        "section_name": section_name,
                        "chunk_id": i,
                        # Add other relevant metadata here
                    }
                }
                chunks.append(chunk)

    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
    except Exception as e:
        logger.error(f"Error reading or processing file {filepath}: {e}")

    return chunks
