import yaml
import os
import logging
import json

from .url_converter import convert_google_sheets_url_to_ods_download, convert_google_doc_url_to_md_download, convert_google_slide_url_to_md_download, convert_file_to_md
from .check.is_existed_not_md import is_existed_not_md
from .check.is_google_sheets_url import is_google_sheets_url
from .check.is_google_doc_url import is_google_doc_url
from .check.is_google_slide_url import is_google_slide_url



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
        
        file_name = f"{knowledge_id}.md"

        url = knowledge_base_config.get('path')
        if url:
            if is_google_sheets_url(url):
                converted_url = convert_google_sheets_url_to_ods_download(url)
                if converted_url != url:
                    logger.info(f"Converted Google Sheets URL to ODS download format: {converted_url}")
                    knowledge_base_config['path'] = converted_url
                    file_name = f"{knowledge_id}.ods"
            elif is_google_doc_url(url):
                converted_url = convert_google_doc_url_to_md_download(url)
                if converted_url != url:
                    logger.info(f"Converted Google Doc URL to Markdown download format: {converted_url}")
                    knowledge_base_config['path'] = converted_url
            elif is_google_slide_url(url):
                converted_url = convert_google_slide_url_to_md_download(url)
                if converted_url != url:
                    logger.info(f"Converted Google Slide URL to Markdown download format: {converted_url}")
                    knowledge_base_config['path'] = converted_url
            elif is_existed_not_md(url):
                converted_url = convert_file_to_md(url)
                if converted_url != url:
                    logger.info(f"Converted File to Markdown format: {converted_url}")
                    knowledge_base_config['path'] = converted_url
            else:
                logger.info(f"URL '{url}' is not a Google Sheets URL, skipping conversion.")
        
        knowledge_base_config['file_name'] = file_name
        # logger.info(f"File name set to: {knowledge_base_config['file_name']}")

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
