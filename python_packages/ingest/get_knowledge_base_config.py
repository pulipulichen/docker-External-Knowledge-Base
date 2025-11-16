import yaml
import os
import logging
from .url_converter import convert_google_sheets_url_to_ods_download

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_knowledge_base_config(knowledge_id):
    config_path = os.path.join(os.path.dirname(__file__), '../../knowledge_base_config.yaml')
    
    if not os.path.exists(config_path):
        logger.error(f"Knowledge base config file not found at {config_path}")
        return None

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    if knowledge_id in config:
        url = config[knowledge_id].get('path')
        if url:
            logger.info(f"Found URL for knowledge_id '{knowledge_id}': {url}")
            
            converted_url = convert_google_sheets_url_to_ods_download(url)
            if converted_url != url:
                logger.info(f"Converted Google Sheets URL to ODS download format: {converted_url}")
            return converted_url
        else:
            logger.warning(f"No 'path' found for knowledge_id '{knowledge_id}' in config.")
            return None
    else:
        logger.warning(f"Knowledge ID '{knowledge_id}' not found in config.")
        return None

if __name__ == '__main__':
    # Example usage
    test_knowledge_id = 'a'
    url = get_knowledge_base_config(test_knowledge_id)
    if url:
        print(f"URL for '{test_knowledge_id}': {url}")
    else:
        print(f"Could not retrieve URL for '{test_knowledge_id}'.")
