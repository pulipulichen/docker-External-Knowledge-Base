import logging
import os

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MARKDOWN_CONVERTER_URL = os.environ.get(
    "MARKDOWN_CONVERTER_URL", "http://markdown_converter:80"
).rstrip("/")
MARKDOWN_CONVERTER_TIMEOUT = int(
    os.environ.get("MARKDOWN_CONVERTER_TIMEOUT", "125")
)


def convert_file_path_to_markdown_content(file_path):
    url = f"{MARKDOWN_CONVERTER_URL}/convert_file_path"
    try:
        response = requests.post(
            url,
            json={"file_path": file_path},
            timeout=MARKDOWN_CONVERTER_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.error(
            "Markdown converter request failed for file_path '%s': %s",
            file_path,
            exc,
        )
        return False

    if response.status_code == 400:
        logger.error(
            "Markdown converter bad request for file_path '%s': %s",
            file_path,
            response.text,
        )
        return False

    if response.status_code != 200:
        logger.error(
            "Markdown converter HTTP %s for file_path '%s': %s",
            response.status_code,
            file_path,
            response.text[:500],
        )
        return False

    try:
        payload = response.json()
    except ValueError:
        logger.error(
            "Markdown converter returned non-JSON for file_path '%s'", file_path
        )
        return False

    if not payload.get("ok"):
        logger.error(
            "Markdown converter conversion failed for file_path '%s': %s",
            file_path,
            payload.get("error", ""),
        )
        return False

    markdown_content = payload.get("markdown")
    if markdown_content is None:
        logger.error(
            "Markdown converter missing markdown field for file_path '%s'", file_path
        )
        return False

    return markdown_content
