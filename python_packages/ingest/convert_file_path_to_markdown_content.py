import logging
import os
import re

md_instance = None
def get_markitdown():
    # 確保只在需要時、且在 Worker process 內才匯入與初始化
    global md_instance
    if md_instance is None:
        from markitdown import MarkItDown
        md_instance = MarkItDown()
    return md_instance

# md = MarkItDown(enable_plugins=False) # Set to True to enable plugins

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def convert_file_path_to_markdown_content(file_path):
    try:
        md = get_markitdown()

        logger.info(f'read: {file_path}')
        os.system(f"cat '{file_path}' > /dev/null")
        os.system(f"cp '{file_path}' /tmp")

        file_path = os.path.join('/tmp', os.path.basename(file_path))

        # 這裡，幫我顯示file_path的大小。如果是0則丟出錯誤

        logger.info(f'tmp path: {file_path}')

        markdown_content = md.convert(file_path)
        markdown_content = markdown_content.text_content

        # 移除 ![alt](data:image/png;base64,...) 格式
        markdown_content = re.sub(r'!\[.*?\]\(data:image\/.*?;base64,.*?\)', '', markdown_content)

        return markdown_content

    except Exception as e:
        logger.error(f"Error converting file for input_file_path '{file_path}': {e}")
        return False