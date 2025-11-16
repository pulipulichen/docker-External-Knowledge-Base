import re

def convert_google_slide_url_to_md_download(url):
    """
    Converts a Google Slides 'edit' or 'view' URL to a Markdown download URL.

    Args:
        url (str): The original Google Slides URL.

    Returns:
        str: The converted Markdown download URL, or the original URL if no conversion is needed.
    """
    # Regex to match Google Slides 'edit' or 'view' URLs and capture the document ID
    match = re.match(r"https://docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)/(?:edit|view)(?:\?usp=sharing)?", url)

    if match:
        doc_id = match.group(1)
        md_url = f"https://docs.google.com/presentation/d/{doc_id}/export/markdown"
        return md_url
    else:
        return url
