import logging
import os
# import json
import datetime

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _latest_content_mtime(path: str) -> datetime.datetime:
    """
    Return the latest modification time for indexing freshness checks.
    For a regular file (or non-directory path), uses that path's mtime.
    For a directory, uses the maximum mtime among all files under path,
    recursively, skipping dotfiles and not descending into dot-prefixed
    directories. If no eligible files exist, falls back to the directory's mtime.
    """
    if not os.path.isdir(path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(path))

    latest_ts: float | None = None
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            fp = os.path.join(dirpath, name)
            try:
                ts = os.path.getmtime(fp)
            except OSError:
                continue
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts

    if latest_ts is None:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return datetime.datetime.fromtimestamp(latest_ts)


def check_file_need_update_automatically(knowledge_id):
    # logger.info(f"Knowledge ID: {knowledge_id}")

    config = get_knowledge_base_config(knowledge_id)
    if config is None:
        logger.error(f"Could not retrieve config for knowledge ID: {knowledge_id}")
        return False
    
    filename = config.get('file_name')
    filepath = config.get('file_path')

    if file_or_valid_symlink(filepath) is False:
        logger.error(f"File not found at path: {filepath}")
        return False

    index_time_filepath = config.get('index_time_filepath')
    last_index_time = None
    if os.path.exists(index_time_filepath):
        try:
            with open(index_time_filepath, 'r') as f:
                timestamp_str = f.read().strip()
                last_index_time = datetime.datetime.fromisoformat(timestamp_str)
                logger.debug(f"Read index time from file: {last_index_time}")
        except Exception as e:
            logger.error(f"Error reading index time from {index_time_filepath}: {e}")

    if last_index_time is not None:
        file_mod_time = _latest_content_mtime(filepath)
        time_difference = file_mod_time - last_index_time

        update_delay_seconds = config.get('auto_update', {}).get('delay_seconds', 30 * 60)

        if last_index_time is not None and time_difference < datetime.timedelta(seconds=update_delay_seconds):
            logger.info(f"Files are up to date. Skipping index. {file_mod_time} - {last_index_time} < {datetime.timedelta(seconds=update_delay_seconds)}")
            return False

    if not filename:
        logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")
        return False
    

    return True

def file_or_valid_symlink(path: str) -> bool:
    # 1. 該路徑本身就是檔案 → True
    if os.path.exists(path):
        # logger.error(f"exists: {path}")
        return True

    # 2. 該路徑是軟連結，且指向的目標存在 → True
    if os.path.islink(path):
        target = os.readlink(path)
        # logger.error(f"target: {target}")
        # 解析成絕對路徑 (處理相對連結與絕對連結)
        abs_target = os.path.join(os.path.dirname(path), target) if not os.path.isabs(target) else target
        # logger.error(f"abs_target: {abs_target}")
        if os.path.exists(abs_target):
            # logger.error(f"abs_target exists: {abs_target}")
            return True

    # 其餘情況 → False
    return False