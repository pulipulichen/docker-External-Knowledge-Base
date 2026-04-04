"""
URL path suffixes treated as non-HTML documents for POST /scrape.

Edit NON_WEB_PAGE_EXTENSIONS below to allow or block more types. Values must be
lowercase, without a leading dot (e.g. "pdf", not ".pdf").
"""

from __future__ import annotations

NON_WEB_PAGE_EXTENSIONS: frozenset[str] = frozenset({
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    "rtf",
    "zip",
    "tar",
    "gz",
    "tgz",
    "bz2",
    "7z",
    "rar",
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "bmp",
    "ico",
    "tif",
    "tiff",
    "mp3",
    "mp4",
    "webm",
    "mkv",
    "mov",
    "avi",
    "exe",
    "dmg",
    "apk",
    "deb",
    "rpm",
})
