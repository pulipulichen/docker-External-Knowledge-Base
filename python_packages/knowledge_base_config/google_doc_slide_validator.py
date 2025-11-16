import re

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
