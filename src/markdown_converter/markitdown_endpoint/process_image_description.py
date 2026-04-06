import base64
import io
import os
import re

from PIL import Image

from .image_describe import image_describe

_MIN_EDGE_PX = int(os.getenv("IMAGE_DESCRIBE_MIN_EDGE_PX", "128"))

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def _image_size_from_base64(base64_data: str) -> tuple[int, int] | None:
    raw = base64_data.strip()
    try:
        pad = len(raw) % 4
        if pad:
            raw += "=" * (4 - pad)
        data = base64.b64decode(raw, validate=False)
    except Exception:
        return None
    try:
        with Image.open(io.BytesIO(data)) as im:
            w, h = im.size
            return (int(w), int(h))
    except Exception:
        return None


def process_image_description(markdown_content: str) -> str:

    # 修正重點：將 !\[\] 改為 !\[.*?\]
    # .*? 會匹配中括號內的任何字元（包括路徑、說明文字或空白）
    pattern = r'!\[.*?\]\(data:image\/([^;]+);base64,([^\)]+)\)'

    def replacer(match):
        base64_data = match.group(2)
        size = _image_size_from_base64(base64_data)
        if size is None:
            return ""
        w, h = size
        if w <= _MIN_EDGE_PX or h <= _MIN_EDGE_PX:
            logger.info("image size is too small: %s", size)
            return ""
        description = image_describe(base64_data)
        logger.info("image description: %s", len(description))
        return f'\n\n```image{description}\n```\n\n'

    return re.sub(pattern, replacer, markdown_content)