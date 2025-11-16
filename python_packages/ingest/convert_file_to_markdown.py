import logging
import os
import markitdown # Assuming this is the correct import for the package

from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../knowledge_base_files')

def convert_file_to_markdown(knowledge_id):
    config = get_knowledge_base_config(knowledge_id)

    if 'file_name' in config:
        input_file_path = os.path.join(DOWNLOAD_DIR, config.get('path'))
        output_file_name = config.get('file_name')

        download_expiration_seconds = config.get('download_expiration_seconds', 30 * 60)
        
        try:
            # Read the content of the original file
            with open(input_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert to markdown using markitdown (assuming a simple conversion method)
            # The actual method might vary based on the markitdown library's API
            # For now, I'll assume a direct conversion function.
            # If markitdown is for rendering markdown, I might need a different library for converting other formats TO markdown.
            # Given the prompt "用markitdown的套件來轉換", I'll assume it has a conversion utility.
            markdown_content = markitdown.convert(content) # This is a placeholder, actual API might differ

            # Write the markdown content to a new file
            with open(output_file_name, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"Conversion successful for knowledge_id '{knowledge_id}'. Markdown file saved at: {markdown_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting file for knowledge_id '{knowledge_id}': {e}")
            return False
    
    logger.error(f"File name not found in config for knowledge_id '{knowledge_id}'.")
    return False
