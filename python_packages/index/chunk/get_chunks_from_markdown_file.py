import tiktoken
from typing import List
import os

import logging

logger = logging.getLogger(__name__)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from .convert_str_to_chunks import convert_str_to_chunks

# 如果token長度超過4096，再兩個換行之後，就切斷成不同chunk
# token長度用gpt4的方式計算

def get_chunks_from_markdown_file(knowledge_id, file_path: str) -> List:    
    config = get_knowledge_base_config(knowledge_id)
    max_tokens = config.get('index.max_tokens', 2048)

    # logger.info(f"markdown1: {file_path}")
    # file_path = "/app/knowledge_base_files/example_document-index/2025/雜談：深刻體會Skype退役了 _ Talk：  Deeply Felt Skype's Retirement - 布丁布丁吃什麼？ (12_27_2025 8：57：40 PM).html.md"
    # logger.info(f"markdown2: {file_path}")
    
    # 讀取file_path的內容到 markdown_content
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    sections = convert_str_to_chunks(markdown_content, max_tokens)

    # logger.info(f"Length of markdown_content: {len(markdown_content)}")
    
    relative_path = get_relative_path(file_path)
    title = relative_path.split('/')[-1]

    chunks = []
    for chunk_count, section in enumerate(sections):
        # logger.info(f"Length of section: {len(section)}")
        # logger.info("section content:" + section)

        chunks.append({
            "chunk_id": f"{knowledge_id}_{relative_path}_{chunk_count}",
            'document': section,
            "metadata": {
                "title": title,
                "path": relative_path
            }
        })

    # logger.info(f"Length of chunks: {len(chunks)}")
    # logger.info(f"Length of sections: {len(sections)}")

    return chunks

def get_relative_path(file_path):
    # file_path 如果裡面包含了 -index/ ，那只取出之後的字串
    marker = "-index/"
    
    relative_path = file_path[:-3]
    if marker in relative_path:
        relative_path = relative_path.split(marker, 1)[1]

    return relative_path
