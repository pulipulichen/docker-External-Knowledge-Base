
import logging

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from .download_file import download_file
from .convert_file_to_markdown import convert_file_to_markdown

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def ingest_data(knowledge_id, query, top_k, score_threshold):

    # logger.info(f"Knowledge ID: {knowledge_id}")
    # logger.info(f"Query: {query}")
    # logger.info(f"Top K: {top_k}")
    # logger.info(f"Score Threshold: {score_threshold}" )

    knowledge_base_config = get_knowledge_base_config(knowledge_id)

    if knowledge_base_config.get('is_url') is True:
        download_file(knowledge_id)
    elif knowledge_base_config.get('is_markdown') is False:
        convert_file_to_markdown(knowledge_id)
