import re

def process_image_description(markdown_content: str) -> str:
    pattern = r'!\[\]\(data:image\/[a-zA-Z]+;base64,[^\)]+\)'
    
    return re.sub(pattern, 'PLACEHOLDER', markdown_content)