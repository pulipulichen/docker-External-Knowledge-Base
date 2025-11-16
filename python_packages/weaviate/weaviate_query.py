from .helper.get_collection import get_collection
from ..helper.get_query_config import get_query_config
from .helper.segment_text import segment_text
from .helper.metadata_to_filters import metadata_to_filters
from .helper.filter_item_distinct import filter_item_distinct
from .helper.convert_to_external_knowledge_response import convert_to_external_knowledge_response
from .helper.get_client import get_client
from .weaviate_add import weaviate_add
import weaviate.classes as wvc

from weaviate.classes.query import MetadataQuery
import os

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

if __name__ == "__main__":
  # This is a test usage example.
  test_knowledge_id = "test_knowledge_base_query"
  
  client = get_client()
  # Clean up previous test data if it exists
  if client.collections.exists(test_knowledge_id):
    client.collections.delete(test_knowledge_id)
    print(f"Cleaned up existing collection: {test_knowledge_id}")

  client.collections.create(
    name=test_knowledge_id,
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
    generative_config=wvc.config.Configure.Generative.openai(),
  )
  print(f"Collection '{test_knowledge_id}' created.")

  test_data_rows = [
    {
      "chunk_id": "doc1_chunk1",
      "document": "The quick brown fox jumps over the lazy dog.",
      "vector": [0.1, 0.1, 0.1],
      "metadata": {"source": "animals.txt", "page": 1, "_item_id": "fox_dog"}
    },
    {
      "chunk_id": "doc1_chunk2",
      "document": "A cat sat on the mat.",
      "vector": [0.2, 0.2, 0.2],
      "metadata": {"source": "animals.txt", "page": 2, "_item_id": "cat_mat"}
    },
    {
      "chunk_id": "doc2_chunk1",
      "document": "The early bird catches the worm.",
      "vector": [0.3, 0.3, 0.3],
      "metadata": {"source": "nature.txt", "page": 1, "_item_id": "bird_worm"}
    },
  ]
  weaviate_add(knowledge_id=test_knowledge_id, data_rows=test_data_rows)
  print(f"Added test data to '{test_knowledge_id}'.")

  # Test 1: Basic query
  print("\n--- Test 1: Basic query for 'fox' ---")
  query_text_1 = "fox"
  # In a real scenario, you would get this vector from an embedding model
  query_vector_1 = [0.11, 0.11, 0.11] 
  results_1 = weaviate_query(knowledge_id=test_knowledge_id, query=query_text_1, vector=query_vector_1)
  print(f"Query for '{query_text_1}' returned {len(results_1)} results:")
  for res in results_1:
    print(f"- Document: {res.get('document')} (Score: {res.get('score')})")

  # Test 2: Query with item_id filter
  print("\n--- Test 2: Query for 'cat' with item_id 'cat_mat' ---")
  query_text_2 = "cat"
  query_vector_2 = [0.21, 0.21, 0.21]
  results_2 = weaviate_query(knowledge_id=test_knowledge_id, query=query_text_2, vector=query_vector_2, item_id="cat_mat")
  print(f"Query for '{query_text_2}' with item_id 'cat_mat' returned {len(results_2)} results:")
  for res in results_2:
    print(f"- Document: {res.get('document')} (Score: {res.get('score')})")

  # Test 3: Query with metadata filter (source)
  print("\n--- Test 3: Query for 'bird' with metadata filter 'source: nature.txt' ---")
  query_text_3 = "bird"
  query_vector_3 = [0.31, 0.31, 0.31]
  results_3 = weaviate_query(knowledge_id=test_knowledge_id, query=query_text_3, vector=query_vector_3, metadata={"source": "nature.txt"})
  print(f"Query for '{query_text_3}' with metadata filter returned {len(results_3)} results:")
  for res in results_3:
    print(f"- Document: {res.get('document')} (Score: {res.get('score')})")

  # Clean up the test collection
  client.collections.delete(test_knowledge_id)
  print(f"\nCleaned up test collection: {test_knowledge_id}")
