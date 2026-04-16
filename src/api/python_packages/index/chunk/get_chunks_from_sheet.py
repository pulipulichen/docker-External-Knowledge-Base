import json
import logging

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from .smart_markdown_splitter import SmartMarkdownSplitter
from .utils.sheet_to_json import sheet_to_json

import os

logger = logging.getLogger(__name__)

def get_chunks_from_sheet(knowledge_id: str, section_name: str, max_tokens: int = 1000) -> list[dict]:
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
        config = get_knowledge_base_config(knowledge_id)
        filepath = config.get('file_path')
        include_fields = config.get('include_fileds', [])

        # ============

        logger.info(f"filepath: {filepath}")

        # 如果 filepath 是連接檔，那就取得原始檔案路徑後再來輸入
        if os.path.islink(filepath):
            # Resolve symlink to actual file path
            filepath = os.path.realpath(filepath)

        os.system(f"cat '{filepath}' > /dev/null")
        os.system(f"cp '{filepath}' /tmp")
        filepath = os.path.join('/tmp', os.path.basename(filepath))

        logger.info(f"filepath after: {filepath}")

        # ============

        json_array = sheet_to_json(filepath, section_name, include_fields)

        effective_max = int(config.get("index.max_tokens", max_tokens))
        splitter = SmartMarkdownSplitter(max_tokens=effective_max)

        logger.info(f"json_array count: {len(json_array)}")

        def chunk_id_for_rows(row_indices: list[int]) -> str:
            if len(row_indices) == 1:
                return f"{knowledge_id}_{section_name}_{row_indices[0]}"
            return f"{knowledge_id}_{section_name}_{row_indices[0]}_{row_indices[-1]}"

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
            if splitter.count_tokens(trial_doc) <= effective_max:
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

