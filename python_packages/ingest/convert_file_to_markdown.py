import logging
import os
import time # Import the time module
from .convert_file_path_to_markdown_content import convert_file_path_to_markdown_content

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../knowledge_base_files')

def convert_file_to_markdown(knowledge_id, force_update: False):
    config = get_knowledge_base_config(knowledge_id)

    if 'file_name' in config:
        input_file_path = os.path.join(FILE_STORAGE_DIR, config.get('path'))
        markdown_file_path = os.path.join(FILE_STORAGE_DIR, config.get('file_name')) # Define markdown_file_path directly

        if force_update is False:
            update_delay_seconds = config.get('auto_update', {}).get('delay_seconds', 30 * 60)

            # 如果 input_file_path 變更時間小於 update_delay_seconds ，那就不變動
            if os.path.exists(markdown_file_path): # Check if markdown file already exists
                if update_delay_seconds == -1:
                    # logger.info("update_delay_seconds is -1 and markdown file already exists. Skipping conversion.")
                    return True # Return True as the file is considered "converted" if it exists and delay is -1

            if os.path.exists(input_file_path) and os.path.exists(markdown_file_path):
                last_modified_time = os.path.getmtime(input_file_path)
                current_time = time.time()
                if (current_time - last_modified_time) < update_delay_seconds:
                    logger.info(f"File '{input_file_path}' was modified recently (within {update_delay_seconds} seconds). Skipping conversion.")
                    return True
            elif not os.path.exists(input_file_path): # Only log error if input file is missing
                logger.error(f"Input file '{input_file_path}' not found for knowledge_id '{knowledge_id}'.")
                return False

        try:
            markdown_content = convert_file_path_to_markdown_content(input_file_path) # This is a placeholder, actual API might differ

            # Write the markdown content to a new file
            with open(markdown_file_path, 'w', encoding='utf-8') as f: # Use markdown_file_path here
                f.write(markdown_content)

            logger.info(f"Conversion successful for knowledge_id '{knowledge_id}'. Markdown file saved at: {markdown_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting file for knowledge_id '{knowledge_id}': {e}")
            return False
    
    logger.error(f"File name not found in config for knowledge_id '{knowledge_id}'.")
    return False
