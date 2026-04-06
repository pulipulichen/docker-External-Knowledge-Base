import logging
import os
import re
import fcntl

# from google import genai

# # 初始化 Gemini
# genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# 定義一個簡單的描述函數（模擬 MarkItDown 需要的 client 介面）
class GeminiWrapper:
    def chat(self, model, messages):
        # # 這裡簡化處理，將 MarkItDown 傳來的圖片與 Prompt 轉給 Gemini
        # response = genai_client.models.generate_content(
        #     model=model,
        #     contents=[messages[-1]["content"]] # 取得最後一個包含圖片與指令的內容
        # )
        # # 回傳符合 OpenAI 格式的 Mock 對象
        class Choice:
            def __init__(self, text): self.message = type('obj', (object,), {'content': text})
        class Response:
            def __init__(self, text): self.choices = [Choice(text)]
        return Response("成功")


md_instance = None
def get_markitdown():
    # 確保只在需要時、且在 Worker process 內才匯入與初始化
    global md_instance
    if md_instance is None:
        from markitdown import MarkItDown
        md_instance = MarkItDown(
            enable_plugins=True,
            llm_client=GeminiWrapper(),
            llm_model="gpt-4o"
        )
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

                file_size = os.path.getsize(file_path)
                if file_size == 0:
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

                logger.info(f'markdown_content: {markdown_content}')

                # 移除 ![alt](data:image/png;base64,...) 格式
                # 20260406-1142 改成保留圖片，因為有些圖片是重要的資訊
                # markdown_content = re.sub(r'!\[.*?\]\(data:image\/.*?;base64,.*?\)', '', markdown_content)

                if len(markdown_content) == 0:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                    raise ValueError(f"convert markdown error or empty: '{file_path}'")

                return markdown_content

            finally:
                # 釋放鎖
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    except Exception as e:
        logger.error(f"Error converting file for input_file_path '{file_path}': {e}")
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        return False
