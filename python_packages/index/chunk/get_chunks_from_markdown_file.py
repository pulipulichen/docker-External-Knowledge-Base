import tiktoken
from typing import List
import os

import logging

logger = logging.getLogger(__name__)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from split_markdown4gpt import split

# 如果token長度超過4096，再兩個換行之後，就切斷成不同chunk
# token長度用gpt4的方式計算

def get_chunks_from_markdown_file(knowledge_id, file_path: str) -> List:    
    config = get_knowledge_base_config(knowledge_id)
    max_tokens = config.get('index.max_tokens', 2048)

    sections = split(file_path, model="gpt-4", limit=max_tokens)
    
    relative_path = get_relative_path(file_path)
    title = relative_path.split('/')[-1]

    chunks = []
    for chunk_count, section in enumerate(sections):
        chunks.append({
            "chunk_id": f"{knowledge_id}_{relative_path}_{chunk_count}",
            'document': section,
            "metadata": {
                "title": title,
                "path": relative_path
            }
        })

    return chunks

def get_relative_path(file_path):
    # file_path 如果裡面包含了 -index/ ，那只取出之後的字串
    marker = "-index/"
    
    relative_path = file_path[:-3]
    if marker in relative_path:
        relative_path = relative_path.split(marker, 1)[1]

    return relative_path
