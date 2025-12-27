import tiktoken
from typing import List
import os

import logging

logger = logging.getLogger(__name__)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

# 如果token長度超過4096，再兩個換行之後，就切斷成不同chunk
# token長度用gpt4的方式計算

def get_chunks_from_markdown_file(knowledge_id, file_path: str) -> List:    
    logger.info(f"get_chunks_from_markdown_file: {file_path}")
    
    encoding = tiktoken.encoding_for_model("gpt-4")
    chunks = []
    current_chunk_lines = []
    current_chunk_tokens = 0

    config = get_knowledge_base_config(knowledge_id)

    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    max_tokens = config.get('index.max_tokens', 2048)
    lines = markdown_content.strip().split('\n')

    chunk_count = 0
    for i, line in enumerate(lines):
        tokens = encoding.encode(line)
        for j in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[j:j + max_tokens]
            chunk_text = encoding.decode(chunk_tokens)

            line_tokens = len(encoding.encode(chunk_text))

            # Check if adding the current line exceeds max_tokens
            # If it does, and we have content in current_chunk_lines, save the current chunk
            # and start a new one with the current line.
            if current_chunk_tokens + line_tokens > max_tokens and current_chunk_lines:
                # chunks.append("\n".join(current_chunk_lines))
                append_to_chunks(chunks, current_chunk_lines, knowledge_id, chunk_count, file_path)
                chunk_count += 1
                current_chunk_lines = []
                current_chunk_tokens = 0

            current_chunk_lines.append(chunk_text)
            current_chunk_tokens += line_tokens

        # If the current line is a double newline (empty line followed by another empty line)
        # or if it's the end of the content, and the current chunk is not empty,
        # save the current chunk.
        if (line.strip() == "" and i + 1 < len(lines) and lines[i+1].strip() == "") or \
            (i == len(lines) - 1 and current_chunk_lines):
            if current_chunk_lines:
                # chunks.append("\n".join(current_chunk_lines))
                append_to_chunks(chunks, current_chunk_lines, knowledge_id, chunk_count, file_path)
                chunk_count += 1
                current_chunk_lines = []
                current_chunk_tokens = 0

    # Add any remaining content as a chunk
    if current_chunk_lines:
        append_to_chunks(chunks, current_chunk_lines, knowledge_id, chunk_count, file_path)

    return chunks

def get_relative_path(file_path):
    # file_path 如果裡面包含了 -index/ ，那只取出之後的字串
    marker = "-index/"
    
    relative_path = file_path[:-3]
    if marker in relative_path:
        relative_path = relative_path.split(marker, 1)[1]

    return relative_path

def append_to_chunks(chunks, lines, knowledge_id, chunk_count, file_path):

    relative_path = get_relative_path(file_path)
    
    title = relative_path.split('/')[-1]

    chunk = {
        "chunk_id": f"{knowledge_id}_{relative_path}_{chunk_count}",
        "document": "\n".join(lines),
        "metadata": {
            "title": title,
            "path": relative_path
        }
    }
    
    chunks.append(chunk)
