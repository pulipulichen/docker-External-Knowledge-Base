import logging
import os
from datetime import datetime, timezone

from weaviate.classes.query import MetadataQuery

from ...weaviate.helper.get_collection import get_collection
from ...weaviate.helper.is_collection_existed import is_collection_existed
from ...weaviate.helper.metadata_to_filters import metadata_to_filters
from ..chunk.get_chunks_from_markdown_file import get_relative_path

logger = logging.getLogger(__name__)


def check_need_update(knowledge_id, markdown_file_path):
    relative_path = get_relative_path(markdown_file_path)
    updated_at = datetime.fromtimestamp(
        os.path.getmtime(markdown_file_path), tz=timezone.utc
    ).isoformat()

    if not is_collection_existed(knowledge_id):
        return True

    filters = metadata_to_filters(
        {
            "path": relative_path,
            "updated_at": updated_at,
        }
    )
    if filters is None:
        return True

    try:
        collection = get_collection(knowledge_id)
        response = collection.query.fetch_objects(
            filters=filters,
            limit=1,
            return_metadata=MetadataQuery(score=False),
        )
        if len(response.objects) > 0:
            return False
        return True
    except Exception:
        logger.exception(
            "check_need_update failed for knowledge_id=%r path=%r; will re-index",
            knowledge_id,
            relative_path,
        )
        return True
