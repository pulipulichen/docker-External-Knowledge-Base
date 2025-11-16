from .helper.get_collection import get_collection
from .helper.metadata_to_filters import metadata_to_filters

def weaviate_item_ready(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  item_id = kwargs.get("item_id", kwargs.get("title", None))

  # print(query, collection_name)

  if item_id == None:
    return False
  
  filters = metadata_to_filters({
    "_item_id": item_id
  })

  # =================================================================

  collection = get_collection(collection_name)
  
  response = collection.data.fetch_objects(
    filters=filters,
    limit=1
  )

  return (len(response.objects) > 0)