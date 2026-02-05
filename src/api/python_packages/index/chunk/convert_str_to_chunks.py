import tiktoken
from typing import List
import os
import re

import logging

logger = logging.getLogger(__name__)

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from split_markdown4gpt import split

MAX_LENGTH= 8000

def convert_str_to_chunks(markdown_content: str, max_tokens: int) -> List:    

    # 我要移除掉 markdown_content 裡面，有用到base64嵌入圖片的地方。就是我的RAG索引不要包含那些base64圖片
    # 移除 ![alt](data:image/png;base64,...) 格式
    markdown_content = re.sub(r'!\[.*?\]\(data:image\/.*?;base64,.*?\)', '', markdown_content)
    
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
