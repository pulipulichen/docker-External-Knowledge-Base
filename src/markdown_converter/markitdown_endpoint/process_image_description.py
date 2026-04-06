import re

from .image_describe import image_describe

def process_image_description(markdown_content: str) -> str:
    pattern = r'!\[\]\(data:image\/([^;]+);base64,([^\)]+)\)'

    def replacer(match):
        base64_data = match.group(2)
        # length = len(base64_data)
        # return f'PLACEHOLDER: {length}: {base64_data[0:20]}...{base64_data[-20:]}'
        description = image_describe(base64_data)
        return f'PLACEHOLDER: {description}'

    return re.sub(pattern, replacer, markdown_content)