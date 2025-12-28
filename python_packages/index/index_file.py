
import os
import logging
import redis
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize Redis client
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# Get Redis expiration from environment variable, default to 30 minutes (1800 seconds)
REDIS_EXPIRATION_SECONDS = int(os.getenv('REDIS_EXPIRATION_SECONDS', 1800))

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

# from ..embedding.get_embedding import get_embedding
from .chunk.get_chunks_from_file import get_chunks_from_file
from .mode.index_mode_all import index_mode_all
from .mode.index_mode_last import index_mode_last
from .index_dir import index_dir

# from ..weaviate.weaviate_add import weaviate_add
from .check_file_need_update_automatically import check_file_need_update_automatically

async def index_file(knowledge_id, section_name, force_update: False):

    # force_update = True

    # logger.info(f"index_file Knowledge ID: {knowledge_id} {force_update} {check_file_need_update_automatically(knowledge_id)}")

    if force_update is False and check_file_need_update_automatically(knowledge_id) is False:
        logger.info("File does not need to be updated automatically.")
        return False

    # ----------------------------
    config = get_knowledge_base_config(knowledge_id)

    index_succesful = False
    if config.get('is_file', True):

        chunks = get_chunks_from_file(knowledge_id, section_name)
        if chunks is None:
            logger.error("Failed to retrieve chunks from file.")
            return False
        
        # logger.info(f"Number of chunks: {len(chunks)}")
        # if chunks:
        #     logger.info(f"First chunk content: {chunks[0]}")
        #     logger.info(f"Last chunk content: {chunks[-1]}")

        index_mode = config.get('index', {}).get('mode', 'all')
        # logger.info(f"Index_mode: {index_mode}")
        # logger.info(f"conifg: {json.dumps(config)}")

        if index_mode == 'all':
            index_succesful = await index_mode_all(knowledge_id, section_name, chunks)
        elif index_mode == 'last':
            index_succesful = await index_mode_last(knowledge_id, section_name, chunks)
    else:
        index_succesful = await index_dir(knowledge_id, force_update)

    # =====================================================
    if index_succesful is True:
        write_index_time(config, knowledge_id)
    

def write_index_time(config, knowledge_id):
    # 把現在的時間寫入index_itme    
    current_time = datetime.datetime.now().isoformat()

    filepath = config.get('file_path')
    index_time_filepath = filepath + '-' + knowledge_id + '.index-time.txt'

    try:
        with open(index_time_filepath, 'w') as f:
            f.write(current_time)
        # logger.info(f"Index time '{current_time}' written to {index_time_filepath}")
    except IOError as e:
        logger.error(f"Failed to write index time to {index_time_filepath}: {e}")
