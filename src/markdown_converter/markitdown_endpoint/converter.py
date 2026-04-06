from markitdown import MarkItDown

_md_instance = None


def get_markitdown():
    """Lazy-init MarkItDown in the current worker process."""
    global _md_instance
    if _md_instance is None:
        _md_instance = MarkItDown()
    return _md_instance


def convert_path_to_markdown(file_path: str) -> str:
    """Run MarkItDown on a local file path; returns extracted markdown text."""
    md = get_markitdown()
    return md.convert(file_path, keep_data_uris=True).text_content
