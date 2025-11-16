
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

def index_file(knowledge_id):

    logger.info(f"Knowledge ID: {knowledge_id}")