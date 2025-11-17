
import logging

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..knowledge_base_config.get_section_name import get_section_name

from .download_file import download_file
from .convert_file_to_markdown import convert_file_to_markdown
from ..index.index_file import index_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def ingest_data(knowledge_id, section_name):

    # logger.info(f"Knowledge ID: {knowledge_id}")
    # logger.info(f"Query: {query}")
    # logger.info(f"Top K: {top_k}")
    # logger.info(f"Score Threshold: {score_threshold}" )

    knowledge_base_config = get_knowledge_base_config(knowledge_id)

    if knowledge_base_config.get('is_url') is True:
        download_file(knowledge_id)
    elif knowledge_base_config.get('markdown_convertable') is True:
        convert_file_to_markdown(knowledge_id)

    if section_name is None:
        section_name = get_section_name(knowledge_id)

    await index_file(knowledge_id, section_name)
