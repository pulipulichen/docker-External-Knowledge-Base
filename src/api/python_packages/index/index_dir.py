import logging
import os
import time # Import the time module


from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..ingest.convert_file_path_to_markdown_content import convert_file_path_to_markdown_content
from ..weaviate.weaviate_clear_relative_path import weaviate_clear_relative_path
from .chunk.get_chunks_from_markdown_file import get_relative_path
from .mode.index_mode_file import index_mode_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# FILE_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../', 'knowledge_base/files')
FILE_STORAGE_DIR = '/app/knowledge_base/files'

async def index_dir(knowledge_id, force_update: False):

    # for debug
    # force_update = True

    config = get_knowledge_base_config(knowledge_id)
    update_delay_seconds = config.get('auto_update', {}).get('delay_seconds', 30 * 60)

    index_result = False

    if 'file_name' not in config:
        return False

    input_dir_path = os.path.join(FILE_STORAGE_DIR, config.get('path'))
    markdown_dir_path = os.path.join(FILE_STORAGE_DIR, '.md', config.get('file_name')) + '-index' # Define markdown_file_path directly

    include_ext = config.get('include_ext')
    if isinstance(include_ext, str):
        include_ext = [include_ext]
    
    # Ensure extensions start with a dot and are lowercase for comparison
    if include_ext:
        include_ext = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in include_ext]

    for root, dirs, files in os.walk(input_dir_path):
        
        for file in files:
            logger.info(f'file: {file}')
            file_path = os.path.join(root, file)
            
            if include_ext:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext not in include_ext:
                    logger.info(f'Skip: {file_path}')
                    continue
            
            # logger.info(f"Processing file: {file_path}")
            markdown_file_path = convert_to_markdown_file_path(file_path, markdown_dir_path)
            
            if force_update is True or check_need_update(file_path, markdown_file_path, update_delay_seconds):
                # 如果沒有 markdown_dir_path ，那就建立
                make_index_dir(markdown_dir_path)

                convert_file_to_markdown(file_path, markdown_file_path)
                if await index_mode_file(knowledge_id, markdown_file_path) is True:
                    index_result = True
                # logger.info(f"Processing file: {markdown_file_path}")

    # 在這裡檢查，如果 markdown_dir_path 底下，有 .md 檔案，但是沒有對應的 file_path ，那就刪除
    for root, dirs, files in os.walk(markdown_dir_path):
        for file in files:
            if not file.endswith('.md'):
                continue

            markdown_file_path = os.path.join(root, file)
            
            # 把 markdown_file_path 的相對路徑，轉換成相對於 input_dir_path 的路徑，並移除 .md 後綴
            relative_path = markdown_file_path[len(markdown_dir_path + '/' + config.get('path')):-3]
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            
            source_path = os.path.join(FILE_STORAGE_DIR, relative_path)
            # if not os.path.exists(source_path):
            logger.info(f"Source file missing for indexed markdown; clearing Weaviate and cache: "
                        f"relative_path={relative_path!r} \n" 
                        f"markdown_file_path={markdown_file_path!r} \n"
                        f"source_path={source_path!r}")
                # weaviate_clear_relative_path(knowledge_id=knowledge_id, relative_path=relative_path)
                # os.remove(markdown_file_path)

    # if cleanup_orphan_indexed_files(knowledge_id, input_dir_path, markdown_dir_path):
    #     index_result = True

    # logger.info(f"markdown_dir_path: '{markdown_dir_path}'")
    return index_result


def cleanup_orphan_indexed_files(knowledge_id, input_dir_path, markdown_dir_path):
    """
    For each cached markdown under markdown_dir_path, if the corresponding source
    file under input_dir_path no longer exists, delete Weaviate rows for that path
    and remove the orphan markdown file.
    """
    if not os.path.isdir(markdown_dir_path):
        return False

    cleaned = False
    for root, _dirs, files in os.walk(markdown_dir_path):
        for name in files:
            if not name.endswith('.md'):
                continue
            markdown_file_path = os.path.join(root, name)
            relative_path = get_relative_path(markdown_file_path)
            source_path = os.path.join(input_dir_path, relative_path)
            if os.path.exists(source_path):
                continue

            logger.info(
                "Source file missing for indexed markdown; clearing Weaviate and cache: "
                f"relative_path={relative_path!r}"
            )
            weaviate_clear_relative_path(knowledge_id=knowledge_id, relative_path=relative_path)
            cleaned = True
            try:
                os.remove(markdown_file_path)
            except OSError as e:
                logger.error(f"Failed to remove orphan markdown file {markdown_file_path!r}: {e}")

    return cleaned


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

    if (file_mtime - markdown_mtime) > update_delay_seconds:
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


ROOT_MARKDOWN_DIR_CHECKED = False
MARKDOWN_DIR_CHECKED = []
def make_index_dir(markdown_dir_path):
    if markdown_dir_path not in MARKDOWN_DIR_CHECKED:
        os.makedirs(markdown_dir_path, exist_ok=True)
        os.chmod(markdown_dir_path, 0o777)
        MARKDOWN_DIR_CHECKED.append(markdown_dir_path)

    global ROOT_MARKDOWN_DIR_CHECKED
    if ROOT_MARKDOWN_DIR_CHECKED is False:
        os.chmod(os.path.dirname(markdown_dir_path), 0o777)
        ROOT_MARKDOWN_DIR_CHECKED = True
