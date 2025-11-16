import re

def is_google_sheets_url(url: str) -> bool:
    """
    Checks if the given URL is a valid Google Sheets URL.
    """
    google_sheets_pattern = re.compile(
        r"^(https?://)?(docs\.google\.com/spreadsheets/d/|drive\.google\.com/file/d/)"
        r"([a-zA-Z0-9_-]+)(/edit|/view|/export|/pub)?.*$"
    )
    return bool(google_sheets_pattern.match(url))

if __name__ == '__main__':
    # Test cases
    test_urls = [
        "https://docs.google.com/spreadsheets/d/12345abcde/edit#gid=0",
        "https://docs.google.com/spreadsheets/d/12345abcde/view",
        "https://drive.google.com/file/d/12345abcde/view",
        "http://docs.google.com/spreadsheets/d/12345abcde/export",
        "https://docs.google.com/spreadsheets/d/12345abcde/pubhtml",
        "https://notgooglesheets.com/spreadsheet",
        "https://docs.google.com/document/d/12345abcde/edit", # Not a spreadsheet
        "invalid-url",
        ""
    ]

    for url in test_urls:
        print(f"'{url}' is a Google Sheets URL: {is_google_sheets_url(url)}")
