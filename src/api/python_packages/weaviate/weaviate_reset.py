import logging

from .helper.get_client import get_client

logger = logging.getLogger(__name__)


def weaviate_reset_all() -> dict:
    """
    Remove every Weaviate collection in the connected instance.

    Returns:
        deleted_collections: sorted names that existed immediately before deletion
        count: number of collections removed
    """
    client = get_client()
    existing = client.collections.list_all(simple=True)
    names = sorted(existing.keys()) if existing else []
    if names:
        client.collections.delete_all()
        logger.info("Weaviate reset: deleted %d collection(s)", len(names))
    else:
        logger.info("Weaviate reset: no collections to delete")
    return {"deleted_collections": names, "count": len(names)}
