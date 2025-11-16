
import os
import logging
import redis

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize Redis client
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# Get Redis expiration from environment variable, default to 30 minutes (1800 seconds)
REDIS_EXPIRATION_SECONDS = int(os.getenv('REDIS_EXPIRATION_SECONDS', 1800))

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../knowledge_base_files')

from ..embedding.get_embedding import get_embedding

def index_file(knowledge_id, section_name):

    # logger.info(f"Knowledge ID: {knowledge_id}")

    config = get_knowledge_base_config(knowledge_id)
    if config is None:
        logger.error(f"Could not retrieve config for knowledge ID: {knowledge_id}")
        return False

    filename = config.get('file_name')
    filepath = os.path.join(FILE_STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        logger.error(f"File not found at path: {filepath}")
        return False

    if filename:
        logger.info(f"Filename for knowledge ID '{knowledge_id}': {filename}")
    else:
        logger.error(f"Filename not found in config for knowledge ID: {knowledge_id}")

    # 我儲存test字串到redis的key test裡面，30分鐘到期。
    # Store 'test' string in Redis with key 'test' and expiration from environment variable
    # redis_client.setex("test", REDIS_EXPIRATION_SECONDS, "test")
    # logger.info(f"Stored 'test' in Redis with a {REDIS_EXPIRATION_SECONDS}-second expiration.")

    
    
