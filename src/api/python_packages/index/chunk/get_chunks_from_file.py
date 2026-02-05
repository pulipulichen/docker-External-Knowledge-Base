import os
import logging
from typing import List, Dict, Any

from ...weaviate.helper.segment_text import segment_text

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from .get_chunks_from_sheet import get_chunks_from_sheet
from .get_chunks_from_markdown import get_chunks_from_markdown

def get_chunks_from_file(knowledge_id: str, section_name: str) -> List[Dict[str, Any]]:
    config = get_knowledge_base_config(knowledge_id)

    filename = config.get('file_name')
    if filename.endswith('.ods') or filename.endswith('.xlsx'):
        chunks = get_chunks_from_sheet(knowledge_id, section_name)
    elif filename.endswith('.md'):
        chunks = get_chunks_from_markdown(knowledge_id)
    
    return chunks
