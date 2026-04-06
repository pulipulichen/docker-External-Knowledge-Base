import re

def process_image_description(markdown_content: str) -> str:
    pattern = r'!\[\]\(data:image\/([^;]+);base64,([^\)]+)\)'

    def replacer(match):
        base64_data = match.group(2)
        length = len(base64_data)
        return f'PLACEHOLDER: {length}'

    return re.sub(pattern, replacer, markdown_content)