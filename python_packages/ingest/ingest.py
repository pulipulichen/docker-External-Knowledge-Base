
import logging
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def ingest_data(knowledge_id, query, top_k, score_threshold):

    logger.info(f"Knowledge ID: {knowledge_id}")
    logger.info(f"Query: {query}")
    logger.info(f"Top K: {top_k}")
    logger.info(f"Score Threshold: {score_threshold}" )

    config = get_knowledge_base_config(knowledge_id)
    if 'path' in config:
        logger.info(f"Retrieved URL for knowledge_id '{knowledge_id}': {config.get('path')}")
        # Further ingestion logic using the URL would go here
    else:
        logger.error(f"Failed to retrieve URL for knowledge_id '{knowledge_id}'. Aborting ingestion.")
        return # Or raise an exception, depending on desired error handling
