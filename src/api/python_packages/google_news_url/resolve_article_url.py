"""將 news.google.com 文章包裝網址解成發布者原文 URL（例如供 RSS / Mercury 使用）。"""

import logging
from urllib.parse import urlparse

from googlenewsdecoder import gnewsdecoder


def resolve_google_news_article_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host != "news.google.com":
        return url
    try:
        out = gnewsdecoder(url, interval=0)
        if out.get("status") and isinstance(out.get("decoded_url"), str):
            return out["decoded_url"]
        logging.warning("Google News decode failed for url: %s — %s", url, out)
    except Exception:
        logging.exception("Google News decode raised for url: %s", url)
    return url
