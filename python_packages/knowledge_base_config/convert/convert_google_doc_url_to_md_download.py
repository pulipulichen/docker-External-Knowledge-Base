import re

def convert_google_doc_url_to_md_download(url):
    """
    Converts a Google Docs 'edit' or 'view' URL to a Markdown download URL.

    Args:
        url (str): The original Google Docs URL.

    Returns:
        str: The converted Markdown download URL, or the original URL if no conversion is needed.
    """
    # Regex to match Google Docs 'edit' or 'view' URLs and capture the document ID
    match = re.match(r"https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)/(?:edit|view)(?:\?usp=sharing)?", url)

    if match:
        doc_id = match.group(1)
        md_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt&id={doc_id}&exportFormat=txt"
        return md_url
    else:
        return url
