
import os
import logging
import redis
import json
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize Redis client
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# Get Redis expiration from environment variable, default to 30 minutes (1800 seconds)
REDIS_EXPIRATION_SECONDS = int(os.getenv('REDIS_EXPIRATION_SECONDS', 1800))

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from ..embedding.get_embedding import get_embedding
from .chunk.get_chunks_from_file import get_chunks_from_file
from .mode.index_mode_all import index_mode_all
from .mode.index_mode_last import index_mode_last

from ..weaviate.weaviate_add import weaviate_add

async def index_file(knowledge_id, section_name):

    # logger.info(f"Knowledge ID: {knowledge_id}")

    config = get_knowledge_base_config(knowledge_id)
    if config is None:
        logger.error(f"Could not retrieve config for knowledge ID: {knowledge_id}")
        return False

    filename = config.get('file_name')
    filepath = config.get('file_path')
    if not os.path.exists(filepath):
        logger.error(f"File not found at path: {filepath}")
        return False

    index_time_filepath = filepath + '-' + knowledge_id + '.index-time.txt'
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
        file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
        time_difference = file_mod_time - last_index_time

        update_delay_seconds = config.get('update_delay_seconds', 30 * 60)

        if last_index_time is not None and time_difference < datetime.timedelta(seconds=update_delay_seconds):
            logger.info("File is up to date. Skipping index.")
            return False

    # if filename:
    #     logger.info(f"Filename for knowledge ID '{knowledge_id}': {filename}")
    # else:
    #     logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")
    if not filename:
        logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")

    chunks = get_chunks_from_file(knowledge_id, section_name)
    if chunks is None:
        logger.error("Failed to retrieve chunks from file.")
        return False
    
    # logger.info(f"Number of chunks: {len(chunks)}")
    # if chunks:
    #     logger.info(f"First chunk content: {chunks[0]}")
    #     logger.info(f"Last chunk content: {chunks[-1]}")

    index_mode = config.get('index.mode', "all")
    if index_mode == 'all':
        await index_mode_all(knowledge_id, section_name, chunks)
    elif index_mode == 'last':
        await index_mode_last(knowledge_id, section_name, chunks)

    # =====================================================
    # 把現在的時間寫入index_itme    
    current_time = datetime.datetime.now().isoformat()
    try:
        with open(index_time_filepath, 'w') as f:
            f.write(current_time)
        # logger.info(f"Index time '{current_time}' written to {index_time_filepath}")
    except IOError as e:
        logger.error(f"Failed to write index time to {index_time_filepath}: {e}")
