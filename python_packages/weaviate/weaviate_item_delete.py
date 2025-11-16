from .helper.get_collection import get_collection
from .helper.metadata_to_filters import metadata_to_filters

import os

def weaviate_item_delete(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)

  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base') 
  # weaviate_collection_delete(collection_name=collection_name)
  
  item_id = kwargs.get("item_id", kwargs.get("title", None))

  # print({"query": item_id, "collection_name": collection_name})

  if item_id == None:
    return False
  
  filters = metadata_to_filters({
    "_item_id": item_id
  })

  # =================================================================

  collection = get_collection(collection_name)
  
  # print({"filters": filters})

  try:
    # print("get", collection.data.get(
    #   where=filters
    # ))

    return collection.data.delete_many(
      where=filters
    )
  except Exception as e:
    # print(f"Error deleting item: {e}")
    return False