import tiktoken
from typing import List
import os

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

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
    encoding = tiktoken.encoding_for_model("gpt-4")
    chunks = []
    current_chunk_lines = []
    current_chunk_tokens = 0

    config = get_knowledge_base_config(knowledge_id)
    file_path = config.get('file_path')

    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    max_tokens = config.get('index.max_tokens', 4096)
    lines = markdown_content.split('\n')

    chunk_count = 0
    for i, line in enumerate(lines):
        line_tokens = len(encoding.encode(line))

        # Check if adding the current line exceeds max_tokens
        # If it does, and we have content in current_chunk_lines, save the current chunk
        # and start a new one with the current line.
        if current_chunk_tokens + line_tokens > max_tokens and current_chunk_lines:
            chunks.append("\n".join(current_chunk_lines))
            current_chunk_lines = []
            current_chunk_tokens = 0

        current_chunk_lines.append(line)
        current_chunk_tokens += line_tokens

        # If the current line is a double newline (empty line followed by another empty line)
        # or if it's the end of the content, and the current chunk is not empty,
        # save the current chunk.
        if (line.strip() == "" and i + 1 < len(lines) and lines[i+1].strip() == "") or \
           (i == len(lines) - 1 and current_chunk_lines):
            if current_chunk_lines:
                # chunks.append("\n".join(current_chunk_lines))
                append_to_chunks(chunks, current_chunk_lines, knowledge_id, chunk_count)
                chunk_count += 1
                current_chunk_lines = []
                current_chunk_tokens = 0

    # Add any remaining content as a chunk
    if current_chunk_lines:
        append_to_chunks(chunks, current_chunk_lines, knowledge_id, chunk_count)

    return chunks

def append_to_chunks(chunks, lines, knowledge_id, chunk_count):
    chunk = {
        "chunk_id": f"{knowledge_id}_{chunk_count}",
        "document": "\n".join(lines),
    }
    chunks.append(chunk)
