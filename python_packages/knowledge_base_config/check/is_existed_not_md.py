import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# def is_existed_not_md(file_path):
#     """
#     Checks if a local file exists and is not a markdown file.
#     """
#     if os.path.exists(file_path) and not file_path.lower().endswith('.md'):
#         return True
#     return False

def is_existed_not_md(url):
    """
    Checks if a given URL points to an existing file that is NOT a Markdown file.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        # Check if the file exists
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Check if it's a markdown content type
            if 'text/markdown' in content_type or 'text/x-markdown' in content_type:
                logger.info(f"URL '{url}' is an existing Markdown file (Content-Type: {content_type}).")
                return False
            
            # Check if the URL path ends with .md
            if url.lower().endswith('.md'):
                logger.info(f"URL '{url}' is an existing Markdown file (ends with .md).")
                return False
            
            logger.info(f"URL '{url}' exists and is not a Markdown file (Content-Type: {content_type}).")
            return True
        else:
            logger.info(f"URL '{url}' does not exist or returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error checking URL '{url}': {e}")
        return False
