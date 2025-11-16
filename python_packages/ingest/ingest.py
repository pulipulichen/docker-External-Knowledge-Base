
import logging
import os

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from .download_file import download_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def ingest_data(knowledge_id, query, top_k, score_threshold):

    # logger.info(f"Knowledge ID: {knowledge_id}")
    # logger.info(f"Query: {query}")
    # logger.info(f"Top K: {top_k}")
    # logger.info(f"Score Threshold: {score_threshold}" )

    download_file(knowledge_id)
