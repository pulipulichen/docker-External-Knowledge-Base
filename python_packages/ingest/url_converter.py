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

if __name__ == '__main__':
    # Example usage
    test_url_edit = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit?usp=sharing"
    test_url_other = "https://www.example.com/document"
    test_url_no_usp = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit"

    converted_url_edit = convert_google_sheets_url_to_ods_download(test_url_edit)
    converted_url_other = convert_google_sheets_url_to_ods_download(test_url_other)
    converted_url_no_usp = convert_google_sheets_url_to_ods_download(test_url_no_usp)

    print(f"Original (edit): {test_url_edit}")
    print(f"Converted (ods): {converted_url_edit}")
    print("-" * 30)
    print(f"Original (other): {test_url_other}")
    print(f"Converted (other): {converted_url_other}")
    print("-" * 30)
    print(f"Original (no usp): {test_url_no_usp}")
    print(f"Converted (no usp): {converted_url_no_usp}")
