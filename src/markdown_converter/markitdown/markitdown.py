import fcntl
import importlib.util
import logging
import os
import sys

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_md_instance = None

# This package lives at .../markitdown/; skip it when resolving the PyPI `markitdown` install.
_LOCAL_MARKITDOWN_PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_mark_it_down_class():
    """Import MarkItDown from site-packages; local package name would shadow pip otherwise."""
    for entry in sys.path:
        if not entry:
            entry = os.getcwd()
        candidate = os.path.join(os.path.abspath(entry), "markitdown")
        if os.path.abspath(candidate) == os.path.abspath(_LOCAL_MARKITDOWN_PKG_DIR):
            continue
        init_py = os.path.join(candidate, "__init__.py")
        if os.path.isfile(init_py):
            spec = importlib.util.spec_from_file_location("_markitdown_pypi", init_py)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.MarkItDown
    raise ImportError("MarkItDown not found in sys.path (site-packages)")


def get_markitdown():
    """Lazy-init MarkItDown in the current worker process."""
    global _md_instance
    if _md_instance is None:
        MarkItDown = _load_mark_it_down_class()
        _md_instance = MarkItDown()
    return _md_instance


def convert_file_path_to_markdown_content(file_path):
    """
    Convert a local filesystem path to markdown text.
    Mirrors ingest.convert_file_path_to_markdown_content (lock, zero-byte workaround, validation).
    Returns markdown str on success, False on failure.
    """
    lock_file_path = "/tmp/convert_file_path_to_markdown_content.lock"

    if not os.path.exists(lock_file_path):
        with open(lock_file_path, "w") as f:
            f.write("")

    lock_file = open(lock_file_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        try:
            md = get_markitdown()

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.info("read: %s", file_path)
                os.system(f"cat '{file_path}' > /dev/null")
                os.system(f"cp '{file_path}' /tmp")
                file_path = os.path.join("/tmp", os.path.basename(file_path))

            file_size = os.path.getsize(file_path)
            logger.info("file size: %s bytes", file_size)
            if file_size == 0:
                raise ValueError(f"File '{file_path}' is empty (0 bytes).")

            logger.info("tmp path: %s", file_path)

            markdown_content = md.convert(file_path).text_content

            logger.info("markdown_content: %s", markdown_content)

            if len(markdown_content) == 0:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
                raise ValueError(f"convert markdown error or empty: '{file_path}'")

            return markdown_content

        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)

    except Exception as e:
        logger.error("Error converting file for input_file_path '%s': %s", file_path, e)
        return False

    finally:
        lock_file.close()


convert_bp = Blueprint("markdown_convert", __name__)


@convert_bp.route("/convert_file_path", methods=["POST"])
def convert_file_path_route():
    """POST JSON body: {\"file_path\": \"/absolute/path/on/converter\"}."""
    data = request.get_json(silent=True) or {}
    file_path = data.get("file_path")
    if not file_path or not isinstance(file_path, str):
        return jsonify(ok=False, error="file_path is required and must be a string"), 400

    result = convert_file_path_to_markdown_content(file_path)
    if result is False:
        return jsonify(ok=False, error="conversion failed"), 200

    return jsonify(ok=True, markdown=result), 200
