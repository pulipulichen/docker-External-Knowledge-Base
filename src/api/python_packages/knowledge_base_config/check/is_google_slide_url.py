import re

def is_google_slide_url(url):
    """
    Checks if a given URL is a Google Slides URL.
    """
    return re.match(r"https://docs\.google\.com/presentation/d/[a-zA-Z0-9_-]+/(?:edit|view)(?:\?usp=sharing)?", url) is not None
