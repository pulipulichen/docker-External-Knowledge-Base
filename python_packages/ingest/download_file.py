import logging
import requests
import os
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def download_file(knowledge_id):
    config = get_knowledge_base_config(knowledge_id)

    if 'path' in config:
        logger.info(f"Retrieved URL for knowledge_id '{knowledge_id}': {config.get('path')}")
        # Further ingestion logic using the URL would go here

        file_url = config.get('path')
        if file_url.startswith('http://') or file_url.startswith('https://'):
            logger.info("URL is a valid HTTP/HTTPS URL.")
            
            file_name = config.get('file_name')

            download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../knowledge_base_files')
            
            response = requests.get(file_url)
            downloaded_file_path = os.path.join(download_dir, file_name)
            with open(downloaded_file_path, 'wb') as f:
                f.write(response.content)

            if downloaded_file_path:
                logger.info(f"Ingestion successful for knowledge_id '{knowledge_id}'. File saved at: {downloaded_file_path}")
            else:
                logger.error(f"Ingestion failed for knowledge_id '{knowledge_id}'.")
