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
