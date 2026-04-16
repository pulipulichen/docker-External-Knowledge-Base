import json
import logging
import os

from .utils.sheet_to_json import sheet_to_json
from .utils.get_section_name import get_section_name
from .utils.smart_markdown_splitter import SmartMarkdownSplitter


logger = logging.getLogger(__name__)

def convert_sheet_to_markdown(filepath: str, include_fields: list[str] = [], section_name: str = None, max_tokens: int = 1000) -> list[dict]:

    try:
        chunks = get_chunks_from_sheet(filepath, include_fields, section_name, max_tokens)
        
        # 把 chunks 裡面的 document 轉換成 markdown 內容
        markdown_content = []
        for chunk in chunks:
            markdown_content.append(chunk['document'])
        
        # 把 markdown 內容轉換成 markdown 檔案
        markdown_content = '\n---\n'.join(markdown_content)
        return markdown_content
    except Exception as e:
        logger.error(f"An error occurred in convert_sheet_to_markdown: {e}")
        return []


def get_chunks_from_sheet(filepath: str, include_fields: list[str] = [], section_name: str = None, max_tokens: int = 1000) -> list[dict]:
    """
    Reads an ODS file, extracts data from a specified sheet, and returns chunks.
    The first row of the sheet is used as keys for each row object.
    Consecutive rows are merged into one chunk while the serialized JSON stays within max_tokens
    (tiktoken, same encoder as SmartMarkdownSplitter). A single-row chunk is one JSON object;
    merged chunks are a JSON array of row objects.

    Args:
        knowledge_id (str): The ID of the knowledge base.
        section_name (str): The name of the sheet to extract data from.
        max_tokens (int): Upper bound per chunk before starting a new chunk (overridden by
            config ``index.max_tokens`` when present).

    Returns:
        list[dict]: Each item has ``chunk_id`` and ``document`` (JSON string).
    """
    try:
        # ============

        # 如果 filepath 是連接檔，那就取得原始檔案路徑後再來輸入
        if os.path.islink(filepath):
            # Resolve symlink to actual file path
            filepath = os.path.realpath(filepath)

        os.system(f"cat '{filepath}' > /dev/null")
        os.system(f"cp -f '{filepath}' /tmp")
        filepath = os.path.join('/tmp', os.path.basename(filepath))

        if section_name is None:
            section_name = get_section_name(filepath)
            if section_name is None:
                logger.error(f"Section name is not found in the file: {filepath}")
                return []

        # ============

        json_array = sheet_to_json(filepath, section_name, include_fields)

        splitter = SmartMarkdownSplitter(max_tokens=max_tokens)

        def chunk_id_for_rows(row_indices: list[int]) -> str:
            if len(row_indices) == 1:
                return f"{section_name}_{row_indices[0]}"
            return f"{section_name}_{row_indices[0]}_{row_indices[-1]}"

        def document_for_batch(batch: list[dict]) -> str:
            if len(batch) == 1:
                return json.dumps(batch[0], ensure_ascii=False)
            return json.dumps(batch, ensure_ascii=False)

        chunks: list[dict] = []
        batch: list[dict] = []
        batch_rows: list[int] = []

        for item in json_array:
            row_index = item.pop("__row_index__", 0)

            # 排除掉 item 裡面 value 為空的 key
            item = {k: v for k, v in item.items() if v is not None}
            # logger.info(f"item: {item}")

            if not batch:
                batch.append(item)
                batch_rows.append(row_index)
                continue
            if len(batch) == 1:
                trial_doc = json.dumps([batch[0], item], ensure_ascii=False)
            else:
                trial_doc = json.dumps(batch + [item], ensure_ascii=False)
            if splitter.count_tokens(trial_doc) <= max_tokens:
                batch.append(item)
                batch_rows.append(row_index)
            else:
                chunks.append(
                    {
                        "chunk_id": chunk_id_for_rows(batch_rows),
                        "document": document_for_batch(batch),
                    }
                )
                batch = [item]
                batch_rows = [row_index]

        if batch:
            chunks.append(
                {
                    "chunk_id": chunk_id_for_rows(batch_rows),
                    "document": document_for_batch(batch),
                }
            )
        return chunks

    except Exception as e:
        logger.error(f"An error occurred in get_chunks_from_sheet: {e}")
        return []

