import re
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def is_google_doc_url(url):
    """
    Checks if a given URL is a Google Docs URL.
    """
    return re.match(r"https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+/(?:edit|view)(?:\?usp=sharing)?", url) is not None

def is_google_slide_url(url):
    """
    Checks if a given URL is a Google Slides URL.
    """
    return re.match(r"https://docs\.google\.com/presentation/d/[a-zA-Z0-9_-]+/(?:edit|view)(?:\?usp=sharing)?", url) is not None

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

if __name__ == '__main__':
    # Example usage for Google Docs
    doc_url_edit = "https://docs.google.com/document/d/12345abcde/edit?usp=sharing"
    doc_url_view = "https://docs.google.com/document/d/12345abcde/view"
    doc_url_invalid = "https://docs.google.com/spreadsheets/d/12345abcde/edit"
    
    print(f"'{doc_url_edit}' is Google Doc URL: {is_google_doc_url(doc_url_edit)}")
    print(f"'{doc_url_view}' is Google Doc URL: {is_google_doc_url(doc_url_view)}")
    print(f"'{doc_url_invalid}' is Google Doc URL: {is_google_doc_url(doc_url_invalid)}")

    print("-" * 30)

    # Example usage for Google Slides
    slide_url_edit = "https://docs.google.com/presentation/d/67890fghij/edit?usp=sharing"
    slide_url_view = "https://docs.google.com/presentation/d/67890fghij/view"
    slide_url_invalid = "https://docs.google.com/document/d/67890fghij/edit"

    print(f"'{slide_url_edit}' is Google Slide URL: {is_google_slide_url(slide_url_edit)}")
    print(f"'{slide_url_view}' is Google Slide URL: {is_google_slide_url(slide_url_view)}")
    print(f"'{slide_url_invalid}' is Google Slide URL: {is_google_slide_url(slide_url_invalid)}")
