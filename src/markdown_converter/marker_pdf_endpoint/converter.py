from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered
import base64
import io

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config = {
    "output_format": "markdown"
}
config_parser = ConfigParser(config)
artifact_dict = create_model_dict()
converter = PdfConverter(artifact_dict=artifact_dict)

def convert_file_path_to_markdown_content(file_path):
    rendered = converter(file_path)

    logger.info("rendered: %s", rendered)

    full_text, _, images = text_from_rendered(rendered)
    # 替換 Markdown 中的圖片語法
    # Marker 預設生成的圖片標記通常是 ![](image_name.png)
    final_markdown = full_text

    for img_name, img_data in images.items():
        b64_str = image_to_base64(img_data)
        data_uri = f"data:image/png;base64,{b64_str}"
        
        # 尋找對應的圖片檔名並替換為 base64 字串
        # 注意：需比對 Marker 生成的檔案路徑格式
        final_markdown = final_markdown.replace(img_name, data_uri)

    return rendered

def image_to_base64(img_obj):
    # Marker 的 images 物件通常是 PIL Image
    buffered = io.BytesIO()
    # 根據需求選擇格式，這裡統一轉為 PNG
    img_obj.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')