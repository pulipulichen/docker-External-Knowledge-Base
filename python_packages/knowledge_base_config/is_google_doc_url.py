import re

def is_google_doc_url(url):
    """
    Checks if a given URL is a Google Docs URL.
    """
    return re.match(r"https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+/(?:edit|view)(?:\?usp=sharing)?", url) is not None
