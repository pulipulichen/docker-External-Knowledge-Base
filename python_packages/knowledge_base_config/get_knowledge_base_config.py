import yaml
import os
import logging
from .url_converter import convert_google_sheets_url_to_ods_download
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_knowledge_base_config(knowledge_id):
    config_path = os.path.join(os.path.dirname(__file__), '../../knowledge_base_config.yaml')
    
    if not os.path.exists(config_path):
        logger.error(f"Knowledge base config file not found at {config_path}")
        return {}

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    if knowledge_id in config:
        knowledge_base_config = config.get(knowledge_id)
        logger.info(f"Found URL for knowledge_id '{knowledge_id}': {json.dumps(knowledge_base_config, indent=2)}")
        
        url = knowledge_base_config.get('path')
        if url:
            converted_url = convert_google_sheets_url_to_ods_download(url)
            if converted_url != url:
                logger.info(f"Converted Google Sheets URL to ODS download format: {converted_url}")
                knowledge_base_config['path'] = converted_url
        
        return knowledge_base_config
    else:
        logger.warning(f"Knowledge ID '{knowledge_id}' not found in config.")
        return None

if __name__ == '__main__':
    # Example usage
    test_knowledge_id = 'a'
    result = get_knowledge_base_config(test_knowledge_id)
    if result and result['url']:
        print(f"URL for '{test_knowledge_id}': {result['url']}")
    else:
        print(f"Could not retrieve URL for '{test_knowledge_id}'.")
