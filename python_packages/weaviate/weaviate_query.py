from .helper.get_collection import get_collection
from ..helper.get_query_config import get_query_config
from .helper.segment_text import segment_text
from .helper.metadata_to_filters import metadata_to_filters
from .helper.filter_item_distinct import filter_item_distinct
from .helper.convert_to_external_knowledge_response import convert_to_external_knowledge_response

from weaviate.classes.query import MetadataQuery

def weaviate_query(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  item_id = kwargs.get("item_id", kwargs.get("title", None))
  query = kwargs.get("query", kwargs.get("document", None))
  vector = kwargs.get("vector", [])
  metadata = kwargs.get("metadata", {})

  # print(query, collection_name)

  if query == None or len(vector) == 0:
    return []
  

  # =================================================================

  query_config = kwargs.get("query_config", {})
  query_config = get_query_config(query_config)
  
  query_alpha = query_config.get("query_alpha", 0.5)
  max_results = query_config.get("max_results", 5)
  result_width = query_config.get("result_width", 5)
  score_threshold = query_config.get("score_threshold", 0)
  item_distinct = query_config.get("item_distinct", True) 
  offset = query_config.get("offset", 0) 

  if item_id is not None:
    metadata['_item_id'] = item_id

  filters = metadata_to_filters(metadata) 

  # ================================================================= 

  collection = get_collection(collection_name)
  
  if item_distinct is False:
    limit = max_results

    # print(query)
    # print(score_threshold)
    
    response = collection.query.hybrid(
      query=segment_text(query), 
      vector=vector,
      alpha=query_alpha,
      query_properties=["_index"],
      return_metadata=MetadataQuery(score=True),
      # filters=Filter.by_property("category").equal("音響設備"),
      filters=filters,
      max_vector_distance=(1-score_threshold),
      limit=limit,
      offset=offset
    )
    results = response.objects

  else:
    limit = result_width

    response = collection.query.hybrid(
      query=segment_text(query), 
      vector=vector,
      alpha=query_alpha,
      query_properties=["_index"],
      return_metadata=MetadataQuery(score=True),
      # filters=Filter.by_property("category").equal("音響設備"),
      filters=filters,
      max_vector_distance=score_threshold,
      limit=limit
    )

    results = filter_item_distinct(response)

  return convert_to_external_knowledge_response(results)
  