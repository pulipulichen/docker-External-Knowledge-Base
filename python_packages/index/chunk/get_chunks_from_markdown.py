import tiktoken
from typing import List
import os

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from split_markdown4gpt import split

# 如果token長度超過4096，再兩個換行之後，就切斷成不同chunk
# token長度用gpt4的方式計算

def get_chunks_from_markdown(knowledge_id: str) -> List[str]:    
    """
    Splits markdown content into chunks based on token length and double newlines.

    Args:
        knowledge_id (str): The ID of the knowledge base configuration.

    Returns:
        List[str]: A list of markdown chunks.
    """
    config = get_knowledge_base_config(knowledge_id)
    max_tokens = config.get('index.max_tokens', 2048)

    chunks = []

    config = get_knowledge_base_config(knowledge_id)
    file_path = config.get('file_path')

    sections = split(file_path, model="gpt-4", limit=max_tokens)

    chunks = []
    for chunk_count, section in enumerate(sections):
        chunks.append({
            "chunk_id": f"{knowledge_id}_{chunk_count}",
            'document': section
        })

    return chunks

def append_to_chunks(chunks, lines, knowledge_id, chunk_count):
    chunk = {
        "chunk_id": f"{knowledge_id}_{chunk_count}",
        "document": "\n".join(lines),
    }
    chunks.append(chunk)
