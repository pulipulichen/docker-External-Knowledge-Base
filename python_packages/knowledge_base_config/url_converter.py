import re

def convert_google_sheets_url_to_ods_download(url):
    """
    Converts a Google Sheets 'edit' URL to an 'ods' download URL.

    Args:
        url (str): The original Google Sheets URL.

    Returns:
        str: The converted 'ods' download URL, or the original URL if no conversion is needed.
    """
    # Regex to match Google Sheets 'edit' URLs and capture the document ID
    match = re.match(r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)/edit(?:\?usp=sharing)?", url)

    if match:
        doc_id = match.group(1)
        ods_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=ods"
        return ods_url
    else:
        return url

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

if __name__ == '__main__':
    # Example usage for Google Sheets
    test_url_sheets_edit = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit?usp=sharing"
    test_url_sheets_other = "https://www.example.com/document"
    test_url_sheets_no_usp = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit"

    converted_url_sheets_edit = convert_google_sheets_url_to_ods_download(test_url_sheets_edit)
    converted_url_sheets_other = convert_google_sheets_url_to_ods_download(test_url_sheets_other)
    converted_url_sheets_no_usp = convert_google_sheets_url_to_ods_download(test_url_sheets_no_usp)

    print(f"Original (Sheets edit): {test_url_sheets_edit}")
    print(f"Converted (Sheets ods): {converted_url_sheets_edit}")
    print("-" * 30)
    print(f"Original (Sheets other): {test_url_sheets_other}")
    print(f"Converted (Sheets other): {converted_url_sheets_other}")
    print("-" * 30)
    print(f"Original (Sheets no usp): {test_url_sheets_no_usp}")
    print(f"Converted (Sheets no usp): {converted_url_sheets_no_usp}")
    print("-" * 30)

    # Example usage for Google Docs
    test_url_doc_edit = "https://docs.google.com/document/d/12345abcde/edit?usp=sharing"
    test_url_doc_view = "https://docs.google.com/document/d/12345abcde/view"
    test_url_doc_other = "https://www.example.com/document"

    converted_url_doc_edit = convert_google_doc_url_to_md_download(test_url_doc_edit)
    converted_url_doc_view = convert_google_doc_url_to_md_download(test_url_doc_view)
    converted_url_doc_other = convert_google_doc_url_to_md_download(test_url_doc_other)

    print(f"Original (Doc edit): {test_url_doc_edit}")
    print(f"Converted (Doc md): {converted_url_doc_edit}")
    print("-" * 30)
    print(f"Original (Doc view): {test_url_doc_view}")
    print(f"Converted (Doc md): {converted_url_doc_view}")
    print("-" * 30)
    print(f"Original (Doc other): {test_url_doc_other}")
    print(f"Converted (Doc other): {converted_url_doc_other}")
    print("-" * 30)

    # Example usage for Google Slides
    test_url_slide_edit = "https://docs.google.com/presentation/d/67890fghij/edit?usp=sharing"
    test_url_slide_view = "https://docs.google.com/presentation/d/67890fghij/view"
    test_url_slide_other = "https://www.example.com/presentation"

    converted_url_slide_edit = convert_google_slide_url_to_md_download(test_url_slide_edit)
    converted_url_slide_view = convert_google_slide_url_to_md_download(test_url_slide_view)
    converted_url_slide_other = convert_google_slide_url_to_md_download(test_url_slide_other)

    print(f"Original (Slide edit): {test_url_slide_edit}")
    print(f"Converted (Slide md): {converted_url_slide_edit}")
    print("-" * 30)
    print(f"Original (Slide view): {test_url_slide_view}")
    print(f"Converted (Slide md): {converted_url_slide_view}")
    print("-" * 30)
    print(f"Original (Slide other): {test_url_slide_other}")
    print(f"Converted (Slide other): {converted_url_slide_other}")
