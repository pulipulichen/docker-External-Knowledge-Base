import yaml
import os
import logging
import json

from .check.is_google_sheets_url import is_google_sheets_url
from .check.is_google_doc_url import is_google_doc_url
from .check.is_google_slide_url import is_google_slide_url
# from .check.is_existed_not_md import is_existed_not_md

from .convert.convert_google_sheets_url_to_ods_download import convert_google_sheets_url_to_ods_download
from .convert.convert_google_doc_url_to_md_download import convert_google_doc_url_to_md_download
from .convert.convert_google_slide_url_to_md_download import convert_google_slide_url_to_md_download
# from .convert.convert_file_to_md import convert_file_to_md

FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../', 'knowledge_base_files')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_knowledge_base_config(knowledge_id):
    CONFIG_DIR = os.path.join(os.path.dirname(__file__), '../../', 'knowledge_base_configs')
    config_path = os.path.join(CONFIG_DIR, knowledge_id + '.yml')
    
    if not os.path.exists(config_path):
        config_path = os.path.join(CONFIG_DIR, knowledge_id + '.yaml')

        if not os.path.exists(config_path):
            logger.error(f"Knowledge base config file not found at {config_path}")
            return {}

    with open(config_path, 'r') as file:
        knowledge_base_config = yaml.safe_load(file)

        
    file_name = f"{knowledge_id}.md"

    url = knowledge_base_config.get('path')
    
    is_url = False
    is_file = True
    markdown_convertable = True
    if url and (url.startswith("http://") or url.startswith("https://")):
        is_url = True
        if is_google_sheets_url(url):
            converted_url = convert_google_sheets_url_to_ods_download(url)
            if converted_url != url:
                # logger.info(f"Converted Google Sheets URL to ODS download format: {converted_url}")
                knowledge_base_config['path'] = converted_url
                file_name = f"{knowledge_id}.ods"
                markdown_convertable = False
        elif is_google_doc_url(url):
            converted_url = convert_google_doc_url_to_md_download(url)
            if converted_url != url:
                # logger.info(f"Converted Google Doc URL to Markdown download format: {converted_url}")
                knowledge_base_config['path'] = converted_url
                markdown_convertable = False
        elif is_google_slide_url(url):
            converted_url = convert_google_slide_url_to_md_download(url)
            if converted_url != url:
                # logger.info(f"Converted Google Slide URL to Markdown download format: {converted_url}")
                knowledge_base_config['path'] = converted_url
                markdown_convertable = False
        else:
            logger.info(f"URL '{url}' is not a Google Drive URL, skipping conversion.")
    elif url.endswith('.md') or url.endswith('.ods'):
        file_name = url
        markdown_convertable = False
    elif os.path.isfile(os.path.join(FILE_STORAGE_DIR, url)) is False:
        is_file = False
        file_name = url
        is_url = False
        markdown_convertable = False
    
    knowledge_base_config['file_name'] = file_name

    
    filepath = os.path.join(FILE_STORAGE_DIR, file_name)
    knowledge_base_config['file_path'] = filepath

    knowledge_base_config['is_url'] = is_url
    knowledge_base_config['is_file'] = is_file
    
    knowledge_base_config['markdown_convertable'] = markdown_convertable
    # logger.info(f"File name set to: {knowledge_base_config['file_name']}")

    return knowledge_base_config

if __name__ == '__main__':
    # Example usage
    test_knowledge_id = 'a'
    result = get_knowledge_base_config(test_knowledge_id)
    if result and result['url']:
        print(f"URL for '{test_knowledge_id}': {result['url']}")
    else:
        print(f"Could not retrieve URL for '{test_knowledge_id}'.")
