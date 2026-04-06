import re

from .image_describe import image_describe

def process_image_description(markdown_content: str) -> str:
    pattern = r'!\[\]\(data:image\/([^;]+);base64,([^\)]+)\)'

    def replacer(match):
        base64_data = match.group(2)
        description = image_describe(base64_data)
        return f'`IMAGE: {description}`'

    return re.sub(pattern, replacer, markdown_content)