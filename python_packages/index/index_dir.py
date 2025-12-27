import logging
import os
import time # Import the time module


from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..ingest.convert_file_path_to_markdown_content import convert_file_path_to_markdown_content
from .mode.index_mode_file import index_mode_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../', 'knowledge_base_files')

async def index_dir(knowledge_id, force_update: False):
    config = get_knowledge_base_config(knowledge_id)
    update_delay_seconds = config.get('auto_update', {}).get('delay_seconds', 30 * 60)

    if 'file_name' in config:
        input_dir_path = os.path.join(FILE_STORAGE_DIR, config.get('path'))
        markdown_dir_path = os.path.join(FILE_STORAGE_DIR, config.get('file_name')) + '-index' # Define markdown_file_path directly

        # 如果沒有 markdown_dir_path ，那就建立
        os.makedirs(markdown_dir_path, exist_ok=True)
        os.chmod(markdown_dir_path, 0o777)

        include_ext = config.get('include_ext')
        if isinstance(include_ext, str):
            include_ext = [include_ext]
        
        # Ensure extensions start with a dot and are lowercase for comparison
        if include_ext:
            include_ext = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in include_ext]

        for root, dirs, files in os.walk(input_dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                if include_ext:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext not in include_ext:
                        continue
                
                # logger.info(f"Processing file: {file_path}")
                markdown_file_path = convert_to_markdown_file_path(file_path, markdown_dir_path)
                
                if force_update is True or check_need_update(file_path, markdown_file_path, update_delay_seconds):
                    convert_file_to_markdown(file_path, markdown_file_path)
                    await index_mode_file(knowledge_id, markdown_file_path)
                    # logger.info(f"Processing file: {markdown_file_path}")

        # logger.info(f"markdown_dir_path: '{markdown_dir_path}'")
        return True

    logger.error(f"File name not found in config for knowledge_id '{knowledge_id}'.")
    return False

def convert_to_markdown_file_path(file_path, markdown_dir_path):
    relative_file_path = file_path[len(FILE_STORAGE_DIR):]

    # relative_file_path 再移除第一個 / 前面的字串
    if relative_file_path.startswith('/'):
        relative_file_path = relative_file_path[1:]
    
    if '/' in relative_file_path:
        relative_file_path = relative_file_path[relative_file_path.find('/') + 1:]

    return markdown_dir_path + '/' + relative_file_path + '.md'

def check_need_update(file_path, markdown_file_path, update_delay_seconds):
    # 如果 markdown_file_path 不存在，回覆True
    if not os.path.exists(markdown_file_path):
        return True

    # 如果 file_path 跟 markdown_file_path 的更新日期相差低於 update_delay_seconds ，回覆 True
    # 否則回覆False
    file_mtime = os.path.getmtime(file_path)
    markdown_mtime = os.path.getmtime(markdown_file_path)

    if file_mtime - markdown_mtime > update_delay_seconds:
        return True
    
    return False

def convert_file_to_markdown(input_file_path, markdown_file_path):
    try:
        markdown_content = convert_file_path_to_markdown_content(input_file_path)
        
        # 如果 markdown_file_path 的目錄還沒建起來，幫他建
        os.makedirs(os.path.dirname(markdown_file_path), exist_ok=True)

        # Write the markdown content to a new file
        with open(markdown_file_path, 'w', encoding='utf-8') as f: # Use markdown_file_path here
            f.write(markdown_content)

        # markdown_file_path 權限設為 777
        os.chmod(markdown_file_path, 0o777)

        logger.info(f"Conversion successful for input_file_path '{input_file_path}'. Markdown file saved at: {markdown_file_path}")
        return True

    except Exception as e:
        logger.error(f"Error converting file for input_file_path '{input_file_path}': {e}")
        return False
