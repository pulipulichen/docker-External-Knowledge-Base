import tiktoken
from typing import List
import os

import logging

logger = logging.getLogger(__name__)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from split_markdown4gpt import split

MAX_LENGTH= 8000

def convert_str_to_chunks(markdown_content: str, max_tokens: int) -> List:    
    
    sections = split(markdown_content, model="gpt-4", limit=max_tokens)

    final_sections = []
    for section in sections:
        if len(section) <= MAX_LENGTH:
            final_sections.append(section)
        else:
            # 如果長度超過 MAX_LENGTH，依照 MAX_LENGTH 分割成多塊
            for i in range(0, len(section), MAX_LENGTH):
                final_sections.append(section[i:i + MAX_LENGTH])

    return final_sections
