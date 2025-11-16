
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
from .get_chunks_from_file import get_chunks_from_file

from ..weaviate.weaviate_add import weaviate_add

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

    # This is a test usage example. In a real scenario, these values would come from your application.
    test_knowledge_id = "test_knowledge_base_add"
    
    test_data_rows = [
        {
        "chunk_id": "doc1_chunk1",
        "document": "This is the first part of document one.",
        "vector": [0.1, 0.2, 0.3],
        "metadata": {"source": "doc1.txt", "page": 1, "_item_id": "doc1"}
        },
        {
        "chunk_id": "doc1_chunk2",
        "document": "This is the second part of document one.",
        "vector": [0.4, 0.5, 0.6],
        "metadata": {"source": "doc1.txt", "page": 2, "_item_id": "doc1"}
        },
        {
        "chunk_id": "doc2_chunk1",
        "document": "This is the only part of document two.",
        "vector": [0.7, 0.8, 0.9],
        "metadata": {"source": "doc2.txt", "page": 1, "_item_id": "doc2"}
        },
    ]

    print(f"Attempting to add data to collection: {test_knowledge_id}")
    success = weaviate_add(knowledge_id=test_knowledge_id, data_rows=test_data_rows)

    if success:
        print("weaviate_add test successful!")
        # You can add verification steps here, e.g., query the collection to see if data was added.
    else:
        print("weaviate_add test failed.")

