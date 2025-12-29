import logging
import os
import re
import fcntl

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
    lock_file_path = '/tmp/convert_file_path_to_markdown_content.lock'
    
    # 確保鎖檔案存在
    if not os.path.exists(lock_file_path):
        with open(lock_file_path, 'w') as f:
            f.write("")

    try:
        # 使用 with open 配合 fcntl 進行鎖定
        with open(lock_file_path, 'w') as lock_file:
            # 取得排他鎖 (Exclusive Lock)，若已有其他進程持有鎖，則會在此等待
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            
            try:
                md = get_markitdown()

                logger.info(f'read: {file_path}')
                os.system(f"cat '{file_path}' > /dev/null")
                os.system(f"cp '{file_path}' /tmp")

                file_path = os.path.join('/tmp', os.path.basename(file_path))

                # 這裡，幫我顯示file_path的大小。如果是0則丟出錯誤
                file_size = os.path.getsize(file_path)
                logger.info(f'file size: {file_size} bytes')
                if file_size == 0:
                    raise ValueError(f"File '{file_path}' is empty (0 bytes).")

                logger.info(f'tmp path: {file_path}')

                markdown_content = md.convert(file_path)
                markdown_content = markdown_content.text_content

                # 移除 ![alt](data:image/png;base64,...) 格式
                markdown_content = re.sub(r'!\[.*?\]\(data:image\/.*?;base64,.*?\)', '', markdown_content)

                return markdown_content

            finally:
                # 釋放鎖
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    except Exception as e:
        logger.error(f"Error converting file for input_file_path '{file_path}': {e}")
        return False
